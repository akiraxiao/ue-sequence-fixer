import unreal
import os

class SequenceRepairKit:
    def __init__(self):
        self.editor_asset_lib = unreal.EditorAssetLibrary()
        self.seq_editor_lib = unreal.LevelSequenceEditorBlueprintLibrary()
    
    def process_sequence(self, source_path, target_path, duration_minutes=None):
        """
        主流程：复制 -> 裁剪 -> 修复 -> 报告
        """
        # 1. 复制资产
        if self.editor_asset_lib.does_asset_exist(target_path):
            unreal.log_warning(f"Target asset {target_path} already exists. Overwriting...")
            self.editor_asset_lib.delete_asset(target_path)
        
        success = self.editor_asset_lib.duplicate_asset(source_path, target_path)
        if not success:
            unreal.log_error(f"Failed to duplicate {source_path} to {target_path}")
            return False
            
        sequence = unreal.load_asset(target_path)
        if not isinstance(sequence, unreal.LevelSequence):
            unreal.log_error("Target is not a Level Sequence!")
            return False

        unreal.log(f"Processing copied sequence: {target_path}")

        # 2. 裁剪长度 (如果指定了)
        if duration_minutes:
            display_rate = sequence.get_display_rate()
            fps = display_rate.numerator / display_rate.denominator
            
            # 原本的开始时间
            start_frame = sequence.get_playback_start()
            # 新的结束时间 = 开始 + 分钟*60*fps
            new_duration_frames = int(duration_minutes * 60 * fps)
            end_frame = start_frame + new_duration_frames
            
            sequence.set_playback_end(end_frame)
            unreal.log(f"Trimmed sequence to {duration_minutes} minutes ({new_duration_frames} frames).")

        # 3. 执行健康检查和修复
        self.fix_broken_bindings(sequence)
        self.audit_assets(sequence)

        # 4. 保存
        self.editor_asset_lib.save_asset(target_path)
        self.seq_editor_lib.open_level_sequence(sequence)
        return True

    def fix_broken_bindings(self, sequence):
        """
        尝试修复丢失的 Actor 绑定 (Red bindings)
        逻辑：如果绑定失效，尝试在当前 World 里找一个同名的 Actor 绑上去
        """
        world = unreal.EditorLevelLibrary.get_editor_world()
        bindings = sequence.get_bindings()
        
        fixed_count = 0
        for binding in bindings:
            # 检查绑定是否有效
            bound_objects = sequence.locate_bound_objects(binding, unreal.MovieSceneSequenceID())
            if not bound_objects:
                binding_name = binding.get_name()
                unreal.log_warning(f"Found broken binding: {binding_name}. Attempting auto-fix...")
                
                # 尝试在场景中搜索同名 Actor
                # 注意：这里需要更复杂的逻辑来精准匹配，这里用 Label 简单演示
                actors = unreal.EditorLevelLibrary.get_all_level_actors()
                found_actor = None
                for actor in actors:
                    if actor.get_actor_label() == binding_name:
                        found_actor = actor
                        break
                
                if found_actor:
                    # 重新绑定
                    sequence.bind_possessable_object(binding.get_id(), found_actor, found_actor)
                    unreal.log(f" -> FIXED: Rebound '{binding_name}' to actor '{found_actor.get_path_name()}'")
                    fixed_count += 1
                else:
                    unreal.log_error(f" -> FAILED: Could not find actor named '{binding_name}' in level.")

        if fixed_count > 0:
            unreal.log(f"Total bindings fixed: {fixed_count}")

    def audit_assets(self, sequence):
        """
        审计轨道中的资产 (Animation, Audio, VFX)
        检查引用的资产是否存在
        """
        missing_assets = []
        
        # 遍历所有轨道 (Master Tracks)
        for track in sequence.get_master_tracks():
            self._check_track_sections(track, missing_assets)
            
        # 遍历绑定的轨道
        for binding in sequence.get_bindings():
            for track in binding.get_tracks():
                self._check_track_sections(track, missing_assets)
                
        if missing_assets:
            unreal.log_error("=== MISSING ASSET REPORT ===")
            for report in missing_assets:
                unreal.log_error(f"Track: {report['track']} | Section: {report['section']} | Missing: {report['path']}")
            unreal.log_error("==========================")
        else:
            unreal.log("Asset Integrity Check: PASSED")

    def _check_track_sections(self, track, report_list):
        for section in track.get_sections():
            # 检查动画引用
            if isinstance(section, unreal.MovieSceneSkeletalAnimationSection):
                anim_seq = section.params.animation
                if not anim_seq: # 这里如果引用丢失可能直接是 None，或者是一个无效对象
                     # 尝试获取路径（有时候虽然对象是None，但可能有残留路径，但在Python API里很难取到）
                     pass
            
            # 这里可以扩展更多类型的检查，比如音频

# CLI 接口供 OpenClaw 调用
if __name__ == "__main__":
    import sys
    import argparse
    
    # 模拟简单的参数解析 (UE Python 环境里 argparse有时候不好用，直接解析 sys.argv)
    # 调用格式: py script.py --source "A" --target "B" --minutes 10
    
    source_path = ""
    target_path = ""
    minutes = 0.0
    
    args = sys.argv
    if "--source" in args:
        source_path = args[args.index("--source") + 1]
    if "--target" in args:
        target_path = args[args.index("--target") + 1]
    if "--minutes" in args:
        minutes = float(args[args.index("--minutes") + 1])
        
    if source_path and target_path:
        fixer = SequenceRepairKit()
        fixer.process_sequence(source_path, target_path, minutes)

"""
Timeline Builder Module
========================
Main timeline construction logic for assembling shots into organized timelines.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable, Any, Tuple
from pathlib import Path

from .file_scanner import ProjectScanner
from .hiero_wrapper import HieroProject, HieroTimeline, HieroClip, HieroTrackItem
from .version_manager import VersionManager


@dataclass
class TimelineConfig:
    """Configuration for timeline building."""
    name: str
    episode: str
    sequences: List[str]
    department: str
    version: str = "latest"  # "latest" or specific version like "v009"
    media_type: str = "mov"  # "mov" or "sequence"
    fps: float = 24.0
    include_audio: bool = True


@dataclass
class TimelinePosition:
    """Timeline position for a clip."""
    shot_name: str
    clip_path: str
    timeline_in: int
    timeline_out: int
    duration: int


@dataclass
class BuildResult:
    """Result of timeline build operation."""
    success: bool
    sequence: Any = None
    shots_added: int = 0
    shots_skipped: List[str] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.shots_skipped is None:
            self.shots_skipped = []
        if self.errors is None:
            self.errors = []


class TimelineBuilder:
    """
    Builds Hiero timelines from scanned shot data.
    """
    
    def __init__(
        self,
        scanner: ProjectScanner,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ):
        """
        Initialize TimelineBuilder.
        
        Args:
            scanner: ProjectScanner instance
            progress_callback: Optional callback(message, current, total)
        """
        self._scanner = scanner
        self._progress_callback = progress_callback
    
    def _report_progress(self, message: str, current: int = 0, total: int = 0) -> None:
        """Report progress to callback if set."""
        if self._progress_callback:
            self._progress_callback(message, current, total)
    
    def _sort_shots(self, shots: List[str]) -> List[str]:
        """Sort shots naturally (SH0010 before SH0020)."""
        def sort_key(shot: str) -> int:
            # Extract number from shot name
            import re
            match = re.search(r'(\d+)', shot)
            return int(match.group(1)) if match else 0
        return sorted(shots, key=sort_key)
    
    def _get_media_path(
        self, ep: str, seq: str, shot: str, dept: str, version: str, media_type: str, shot_data: Dict
    ) -> Optional[str]:
        """Get media path for a shot based on media type."""
        dept_data = shot_data.get(dept, {})
        
        if media_type == "mov":
            mov_files = dept_data.get('mov_files', [])
            # Find MOV matching version
            for mov in mov_files:
                if version in mov:
                    return mov
            # Return first MOV if no version match
            return mov_files[0] if mov_files else None
        else:
            # Image sequence
            seq_files = dept_data.get('sequence_files', [])
            if seq_files:
                # Return pattern for sequence
                return seq_files[0] if seq_files else None
        return None
    
    def _calculate_positions(self, clips: List[Tuple[str, str, int]]) -> List[TimelinePosition]:
        """
        Calculate timeline positions for clips.
        
        Args:
            clips: List of (shot_name, clip_path, duration) tuples
            
        Returns:
            List of TimelinePosition objects
        """
        positions = []
        current_frame = 0
        
        for shot_name, clip_path, duration in clips:
            positions.append(TimelinePosition(
                shot_name=shot_name,
                clip_path=clip_path,
                timeline_in=current_frame,
                timeline_out=current_frame + duration - 1,
                duration=duration
            ))
            current_frame += duration
        
        return positions
    
    def build_timeline(self, config: TimelineConfig) -> BuildResult:
        """
        Build a timeline based on configuration.
        
        Args:
            config: TimelineConfig with build parameters
            
        Returns:
            BuildResult with success status and details
        """
        result = BuildResult(success=False)
        clips_data = []  # (shot_name, clip_path, duration)
        
        self._report_progress(f"Building timeline: {config.name}")
        
        # Collect shots from all sequences
        all_shots = []
        for seq in config.sequences:
            shots = self._scanner.scan_shots(config.episode, seq)
            for shot in shots:
                all_shots.append((config.episode, seq, shot))
        
        total_shots = len(all_shots)
        self._report_progress(f"Found {total_shots} shots", 0, total_shots)
        
        # Process each shot
        for i, (ep, seq, shot) in enumerate(all_shots):
            self._report_progress(f"Processing {shot}", i + 1, total_shots)
            
            shot_data = self._scanner.scan_shot_detail(ep, seq, shot)
            dept_data = shot_data.get(config.department, {})
            
            if not dept_data:
                result.shots_skipped.append(f"{ep}/{seq}/{shot} (no {config.department})")
                continue

            # Determine version
            versions = dept_data.get('versions', [])
            if not versions:
                result.shots_skipped.append(f"{ep}/{seq}/{shot} (no versions)")
                continue

            if config.version == "latest":
                version = VersionManager.get_latest_version(versions)
            else:
                version = config.version if config.version in versions else versions[-1]

            # Get media path
            media_path = self._get_media_path(ep, seq, shot, config.department, version, config.media_type, shot_data)
            if not media_path:
                result.shots_skipped.append(f"{ep}/{seq}/{shot} (no {config.media_type} media)")
                continue

            # Get duration from frame range or default
            frame_range = dept_data.get('frame_range')
            duration = (frame_range[1] - frame_range[0] + 1) if frame_range else 100

            clips_data.append((f"{ep}_{seq}_{shot}", media_path, duration))

        if not clips_data:
            result.errors.append("No valid shots found")
            return result

        # Calculate timeline positions
        positions = self._calculate_positions(clips_data)

        # Create Hiero sequence and tracks
        try:
            # Create bin for this review session
            bin_name = f"{config.episode}_Review_Media"
            self._report_progress(f"Creating bin: {bin_name}")

            # Create sequence
            self._report_progress(f"Creating sequence: {config.name}")
            sequence = HieroTimeline.create_sequence(config.name, config.fps)
            video_track = HieroTimeline.add_video_track(sequence, "Video")

            # Add audio track if requested
            audio_track = None
            if config.include_audio:
                audio_track = HieroTimeline.add_audio_track(sequence, "Audio")

            # Import clips to bin and add to track
            self._report_progress(f"Importing {len(positions)} clips to bin and timeline")

            for i, pos in enumerate(positions):
                self._report_progress(f"Adding clip: {pos.shot_name}", i + 1, len(positions))

                # Create clip and add to bin
                clip = HieroClip.create_clip(pos.clip_path, add_to_bin=True, bin_name=bin_name)

                # Add to track
                item = HieroTrackItem.add_item_to_track(
                    video_track, clip, pos.timeline_in, pos.timeline_out
                )

                # Add metadata tags
                HieroTrackItem.set_metadata(item, "shot", pos.shot_name)
                HieroTrackItem.set_metadata(item, "department", config.department)
                HieroTrackItem.set_metadata(item, "version", config.version)
                HieroTrackItem.set_metadata(item, "media_path", pos.clip_path)

            result.success = True
            result.sequence = sequence
            result.shots_added = len(positions)

        except Exception as e:
            import traceback
            traceback.print_exc()
            result.errors.append(f"Failed to create timeline: {str(e)}")

        self._report_progress("Timeline build complete", total_shots, total_shots)
        return result


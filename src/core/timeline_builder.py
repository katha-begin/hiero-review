"""
Timeline Builder Module
========================
Main timeline construction logic for assembling shots into organized timelines.

Structure:
- Media Bin: {EP}/{seq}/ (nested bins)
- Sequence Timeline: {EP}_{seq}_review (contains shots in order)
- Episode Timeline: {EP}_all_review (contains nested sequence timelines)
"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable, Any, Tuple
from pathlib import Path

from .file_scanner import ProjectScanner
from .hiero_wrapper import HieroProject, HieroTimeline, HieroClip, HieroTrackItem
from .version_manager import VersionManager
from ..utils.path_parser import filter_and_sort_shots, sort_sequences


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
    color_space: str = None  # Colorspace for clips (e.g. 'raw', 'ACES', 'sRGB')
    all_sequences: List[str] = None  # All available sequences (to detect if "all" selected)

    def is_all_sequences_selected(self) -> bool:
        """Check if all available sequences are selected."""
        if not self.all_sequences:
            return False
        return set(self.sequences) == set(self.all_sequences)

    def generate_timeline_name(self) -> str:
        """Generate timeline name based on selected sequences."""
        if self.is_all_sequences_selected():
            return f"{self.episode}_all_review"
        else:
            # Join selected sequences: Ep01_sq0010_sq0020_review
            seq_part = "_".join(self.sequences)
            return f"{self.episode}_{seq_part}_review"


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
    shots_updated: int = 0
    shots_skipped: List[str] = None
    errors: List[str] = None
    is_update: bool = False  # True if this was an update to existing timeline

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
        """Sort and filter shots (remove sub-shots like SH0010A, SH0010B)."""
        return filter_and_sort_shots(shots)
    
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
    
    def _scan_shots_for_sequence(self, config: TimelineConfig, seq: str) -> List[Tuple[str, str, str, int]]:
        """
        Scan and collect shot data for a single sequence.

        Args:
            config: TimelineConfig with build parameters
            seq: Sequence name (e.g., 'sq0010')

        Returns:
            List of (shot_name, media_path, version, duration) tuples, sorted by shot order
        """
        clips_data = []
        ep = config.episode

        self._report_progress(f"Scanning sequence: {ep}/{seq}")

        # Get shots and filter out sub-shots (SH0010A, SH0010B), then sort
        raw_shots = self._scanner.scan_shots(ep, seq)
        shots = self._sort_shots(raw_shots)  # Uses filter_and_sort_shots

        self._report_progress(f"  Found {len(shots)} shots (filtered): {shots}")

        for shot in shots:
            shot_data = self._scanner.scan_shot_detail(ep, seq, shot)
            dept_data = shot_data.get(config.department, {})

            if not dept_data:
                continue

            # Determine version
            versions = dept_data.get('versions', [])
            if not versions:
                continue

            if config.version == "latest":
                version = VersionManager.get_latest_version(versions)
            else:
                version = config.version if config.version in versions else versions[-1]

            # Get media path
            media_path = self._get_media_path(ep, seq, shot, config.department, version, config.media_type, shot_data)
            if not media_path:
                continue

            # Get duration from frame range or default
            frame_range = dept_data.get('frame_range')
            duration = (frame_range[1] - frame_range[0] + 1) if frame_range else 100

            shot_name = f"{ep}_{seq}_{shot}"
            clips_data.append((shot_name, media_path, version, duration))

        return clips_data

    def _scan_shots_data(self, config: TimelineConfig) -> List[Tuple[str, str, str, int]]:
        """
        Scan and collect shot data from all sequences.

        Returns:
            List of (shot_name, media_path, version, duration) tuples
        """
        clips_data = []
        self._report_progress(f"Scanner root: {self._scanner._project_root}")

        # Sort sequences by numeric order
        sorted_sequences = sort_sequences(config.sequences)

        for seq in sorted_sequences:
            seq_clips = self._scan_shots_for_sequence(config, seq)
            clips_data.extend(seq_clips)

        self._report_progress(f"Total shots found: {len(clips_data)}")
        return clips_data

    def build_timeline(self, config: TimelineConfig) -> BuildResult:
        """
        Build or update a timeline based on configuration.

        If a sequence with the generated name exists, updates it (adds new shots,
        updates shots with newer versions). Otherwise creates a new sequence.

        Args:
            config: TimelineConfig with build parameters

        Returns:
            BuildResult with success status and details
        """
        result = BuildResult(success=False)

        # Generate timeline name based on selected sequences
        timeline_name = config.generate_timeline_name()
        self._report_progress(f"Timeline name: {timeline_name}")

        # Scan all shot data first
        clips_data = self._scan_shots_data(config)

        if not clips_data:
            result.errors.append("No valid shots found")
            return result

        # Check if sequence already exists
        existing_sequence = HieroTimeline.get_sequence_by_name(timeline_name)

        if existing_sequence:
            self._report_progress(f"Found existing sequence: {timeline_name}")
            return self._update_existing_timeline(config, existing_sequence, timeline_name, clips_data)
        else:
            self._report_progress(f"Creating new sequence: {timeline_name}")
            return self._create_new_timeline(config, timeline_name, clips_data)

    def _get_bin_path_for_shot(self, shot_name: str) -> str:
        """
        Get nested bin path for a shot.

        Args:
            shot_name: Shot name like 'Ep01_sq0010_SH0010'

        Returns:
            Bin path like 'Ep01/sq0010'
        """
        parts = shot_name.split('_')
        if len(parts) >= 2:
            ep = parts[0]   # Ep01
            seq = parts[1]  # sq0010
            return f"{ep}/{seq}"
        return shot_name

    def _check_clip_in_bin(self, bin_path: str, shot_name: str) -> Any:
        """
        Check if a clip for this shot already exists in the bin.

        Args:
            bin_path: Bin path like 'Ep01/sq0010'
            shot_name: Shot name to search for

        Returns:
            Existing clip if found, None otherwise
        """
        existing_clip = HieroClip.find_clip_in_bin(bin_path, shot_name)
        if existing_clip:
            self._report_progress(f"  Found existing clip in bin: {shot_name}")
        return existing_clip

    def _create_new_timeline(self, config: TimelineConfig, timeline_name: str,
                              clips_data: List[Tuple[str, str, str, int]]) -> BuildResult:
        """Create a brand new timeline with all clips."""
        result = BuildResult(success=False, is_update=False)

        try:
            # Create sequence
            sequence = HieroTimeline.create_sequence(timeline_name, config.fps)
            video_track = HieroTimeline.add_video_track(sequence, "Video")

            # Add audio track if requested
            audio_track = None
            if config.include_audio:
                audio_track = HieroTimeline.add_audio_track(sequence, "Audio")

            # Import clips to bin and add to track
            self._report_progress(f"Importing {len(clips_data)} clips to bin and timeline")

            current_frame = 0  # Track current timeline position
            shots_added = 0
            shots_skipped = 0

            for i, (shot_name, media_path, version, _) in enumerate(clips_data):
                self._report_progress(f"Adding clip: {shot_name}", i + 1, len(clips_data))

                # Determine bin path: {EP}/{seq}
                bin_path = self._get_bin_path_for_shot(shot_name)
                self._report_progress(f"  Bin path: {bin_path}")

                # Check if clip already exists in bin
                clip = self._check_clip_in_bin(bin_path, shot_name)

                if clip:
                    # Use existing clip from bin
                    shots_skipped += 1
                    self._report_progress(f"  Using existing clip from bin: {shot_name}")
                else:
                    # Create new clip and add to bin (with colorspace if set)
                    clip = HieroClip.create_clip(
                        media_path,
                        add_to_bin=True,
                        bin_name=bin_path,  # Nested bin path: Ep01/sq0010
                        color_space=config.color_space
                    )
                    self._report_progress(f"  Imported new clip: {shot_name}")

                # Add to VIDEO track at current position (uses clip's actual source duration)
                video_item = HieroTrackItem.add_item_to_track(
                    video_track, clip, current_frame
                )

                # Add metadata tags to video item
                HieroTrackItem.set_metadata(video_item, "shot", shot_name)
                HieroTrackItem.set_metadata(video_item, "department", config.department)
                HieroTrackItem.set_metadata(video_item, "version", version)
                HieroTrackItem.set_metadata(video_item, "media_path", media_path)

                # Get duration from the track item (more accurate than clip)
                item_duration = HieroTrackItem.get_duration(video_item)

                # Add to AUDIO track if enabled (MOV files have embedded audio)
                if audio_track and config.include_audio:
                    if media_path.lower().endswith('.mov'):
                        audio_item = HieroTrackItem.add_item_to_track(
                            audio_track, clip, current_frame, is_audio=True
                        )
                        HieroTrackItem.set_metadata(audio_item, "shot", shot_name)

                # Advance timeline position using track item duration
                current_frame += item_duration
                shots_added += 1

            result.success = True
            result.sequence = sequence
            result.shots_added = shots_added
            self._report_progress(f"Clips imported: {shots_added - shots_skipped}, reused from bin: {shots_skipped}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            result.errors.append(f"Failed to create timeline: {str(e)}")

        self._report_progress("Timeline build complete")
        return result

    def _update_existing_timeline(self, config: TimelineConfig, sequence: Any,
                                   timeline_name: str, clips_data: List[Tuple[str, str, str, int]]) -> BuildResult:
        """
        Update existing timeline - add missing shots and update newer versions.
        """
        result = BuildResult(success=False, is_update=True)

        try:
            # Get existing track items
            existing_items = HieroTimeline.get_track_items(sequence)
            self._report_progress(f"Found {len(existing_items)} existing shots in timeline")

            # Get tracks
            video_track = HieroTimeline.get_video_track(sequence)
            audio_track = HieroTimeline.get_audio_track(sequence)

            if not video_track:
                result.errors.append("No video track found in existing sequence")
                return result

            # Find the end position of existing timeline
            end_frame = 0
            for item_name, item in existing_items.items():
                try:
                    item_end = item.timelineOut()
                    if item_end > end_frame:
                        end_frame = item_end
                except:
                    pass

            shots_added = 0
            shots_updated = 0

            for shot_name, media_path, version, duration in clips_data:
                # Determine bin path: {EP}/{seq}
                bin_path = self._get_bin_path_for_shot(shot_name)

                if shot_name in existing_items:
                    # Shot exists - check if version is newer
                    existing_item = existing_items[shot_name]
                    existing_version = HieroTimeline.get_track_item_version(existing_item)

                    if existing_version and version != existing_version:
                        # Version changed - update the clip
                        self._report_progress(f"Updating {shot_name}: {existing_version} -> {version}")

                        # Get existing position
                        try:
                            timeline_in = existing_item.timelineIn()
                        except:
                            timeline_in = end_frame + 1

                        # Remove old item
                        HieroTimeline.remove_track_item(video_track, existing_item)

                        # Check if clip exists in bin first
                        clip = self._check_clip_in_bin(bin_path, shot_name)
                        if not clip:
                            # Create new clip with updated version
                            clip = HieroClip.create_clip(
                                media_path, add_to_bin=True, bin_name=bin_path,
                                color_space=config.color_space
                            )

                        # Add to track at same position
                        video_item = HieroTrackItem.add_item_to_track(
                            video_track, clip, timeline_in
                        )
                        HieroTrackItem.set_metadata(video_item, "shot", shot_name)
                        HieroTrackItem.set_metadata(video_item, "department", config.department)
                        HieroTrackItem.set_metadata(video_item, "version", version)
                        HieroTrackItem.set_metadata(video_item, "media_path", media_path)

                        # Update audio track too
                        if audio_track and config.include_audio and media_path.lower().endswith('.mov'):
                            audio_item = HieroTrackItem.add_item_to_track(
                                audio_track, clip, timeline_in, is_audio=True
                            )
                            HieroTrackItem.set_metadata(audio_item, "shot", shot_name)

                        shots_updated += 1
                    else:
                        self._report_progress(f"Skipping {shot_name}: already at {version}")
                else:
                    # New shot - add at end of timeline
                    self._report_progress(f"Adding new shot: {shot_name}")

                    timeline_in = end_frame + 1

                    # Check if clip exists in bin first
                    clip = self._check_clip_in_bin(bin_path, shot_name)
                    if not clip:
                        # Create new clip
                        clip = HieroClip.create_clip(
                            media_path, add_to_bin=True, bin_name=bin_path,
                            color_space=config.color_space
                        )

                    # Add to video track
                    video_item = HieroTrackItem.add_item_to_track(
                        video_track, clip, timeline_in
                    )
                    HieroTrackItem.set_metadata(video_item, "shot", shot_name)
                    HieroTrackItem.set_metadata(video_item, "department", config.department)
                    HieroTrackItem.set_metadata(video_item, "version", version)
                    HieroTrackItem.set_metadata(video_item, "media_path", media_path)

                    # Get duration from track item
                    item_duration = HieroTrackItem.get_duration(video_item)

                    # Add to audio track
                    if audio_track and config.include_audio and media_path.lower().endswith('.mov'):
                        audio_item = HieroTrackItem.add_item_to_track(
                            audio_track, clip, timeline_in, is_audio=True
                        )
                        HieroTrackItem.set_metadata(audio_item, "shot", shot_name)

                    # Update end_frame based on track item duration
                    end_frame = timeline_in + item_duration - 1

                    shots_added += 1

            result.success = True
            result.sequence = sequence
            result.shots_added = shots_added
            result.shots_updated = shots_updated

        except Exception as e:
            import traceback
            traceback.print_exc()
            result.errors.append(f"Failed to update timeline: {str(e)}")

        self._report_progress("Timeline update complete")
        return result


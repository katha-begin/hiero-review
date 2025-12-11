"""
Lighting Importer Module
=========================
Imports selected lighting renders to timeline2 at the same timecode as source.
"""
from typing import List, Optional, Any
from dataclasses import dataclass, field

try:
    import hiero.core
    import hiero.ui
    HIERO_AVAILABLE = True
except ImportError:
    HIERO_AVAILABLE = False

from ..core.lighting_scanner import RenderPassInfo
from ..core.hiero_wrapper import (
    HieroProject, HieroTimeline, HieroClip, HieroTrackItem
)


@dataclass
class ImportResult:
    """Result of lighting import operation."""
    success: bool
    clips_added: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class LightingImporter:
    """
    Imports lighting render passes to timeline2.
    
    Creates timeline2 if it doesn't exist, then adds the selected
    render passes at the same timecode as the source item.
    """
    
    TIMELINE2_NAME = "timeline2"
    
    def __init__(self):
        """Initialize LightingImporter."""
        pass
    
    def import_to_timeline2(
        self,
        source_item: Any,
        render_passes: List[RenderPassInfo],
        shot_name: str,
        department_name: str = "lighting"
    ) -> ImportResult:
        """
        Import render passes to timeline2 at the same timecode as source.
        
        Args:
            source_item: Source track item (for timecode reference)
            render_passes: List of RenderPassInfo to import
            shot_name: Shot name for clip naming
            department_name: Department name for clip naming
            
        Returns:
            ImportResult with status and counts
        """
        result = ImportResult(success=True)
        
        if not render_passes:
            result.success = False
            result.errors.append("No render passes selected")
            return result
        
        try:
            # Get source item's timeline position
            timeline_in = self._get_timeline_in(source_item)
            
            # Get or create timeline2
            timeline2 = self._get_or_create_timeline2(source_item)
            if not timeline2:
                result.success = False
                result.errors.append("Failed to get or create timeline2")
                return result
            
            # Get or create video track in timeline2
            video_track = self._get_or_create_video_track(timeline2, department_name)
            if not video_track:
                result.success = False
                result.errors.append("Failed to get or create video track")
                return result
            
            # Import each render pass
            for render_pass in render_passes:
                try:
                    clip_name = f"{shot_name}_{department_name}_{render_pass.name}"
                    self._import_render_pass(
                        render_pass, video_track, timeline_in, clip_name
                    )
                    result.clips_added += 1
                except Exception as e:
                    result.warnings.append(f"Failed to import {render_pass.name}: {e}")
            
            if result.clips_added == 0:
                result.success = False
                result.errors.append("No clips were imported")
                
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
        
        return result
    
    def _get_timeline_in(self, source_item: Any) -> int:
        """Get the timeline in-point of the source item."""
        if HIERO_AVAILABLE:
            return source_item.timelineIn()
        return getattr(source_item, 'timeline_in', 0)
    
    def _get_or_create_timeline2(self, source_item: Any) -> Any:
        """
        Get existing timeline2 or create a new one.
        
        Uses the same sequence (timeline) that contains the source item
        as reference for settings.
        """
        if not HIERO_AVAILABLE:
            return None
        
        # First, check if timeline2 already exists
        existing = HieroTimeline.get_sequence_by_name(self.TIMELINE2_NAME)
        if existing:
            print(f"[LightingImporter] Using existing {self.TIMELINE2_NAME}")
            return existing
        
        # Get source sequence for reference (fps, etc.)
        source_sequence = self._get_source_sequence(source_item)
        fps = 24.0
        if source_sequence:
            try:
                fps = source_sequence.framerate().toFloat()
            except:
                pass
        
        # Create timeline2
        print(f"[LightingImporter] Creating {self.TIMELINE2_NAME}")
        timeline2 = HieroTimeline.create_sequence(self.TIMELINE2_NAME, fps)
        return timeline2
    
    def _get_source_sequence(self, source_item: Any) -> Any:
        """Get the sequence containing the source item."""
        if not HIERO_AVAILABLE:
            return None
        try:
            return source_item.parentSequence()
        except:
            return None

    def _get_or_create_video_track(self, timeline: Any, track_name: str) -> Any:
        """Get existing video track or create a new one."""
        if not HIERO_AVAILABLE:
            return None

        # Look for existing track with this name
        for track in timeline.videoTracks():
            if track.name() == track_name:
                print(f"[LightingImporter] Using existing track: {track_name}")
                return track

        # Create new track
        print(f"[LightingImporter] Creating track: {track_name}")
        return HieroTimeline.add_video_track(timeline, track_name)

    def _import_render_pass(
        self,
        render_pass: RenderPassInfo,
        track: Any,
        timeline_in: int,
        clip_name: str
    ) -> Any:
        """
        Import a single render pass to the track.

        Args:
            render_pass: RenderPassInfo with sequence pattern
            track: Video track to add to
            timeline_in: Timeline position
            clip_name: Name for the clip

        Returns:
            Created track item
        """
        if not HIERO_AVAILABLE:
            return None

        # Create clip from image sequence
        # Use Hiero pattern (file.####.exr)
        pattern = render_pass.hiero_pattern
        frame_range = (render_pass.start_frame, render_pass.end_frame)

        print(f"[LightingImporter] Importing sequence: {pattern}")
        print(f"[LightingImporter] Frame range: {frame_range}")
        print(f"[LightingImporter] Timeline position: {timeline_in}")

        # Create the clip using HieroClip
        clip = HieroClip.create_from_sequence(
            pattern,
            frame_range,
            add_to_bin=True
        )

        if not clip:
            raise Exception(f"Failed to create clip from {pattern}")

        # Add to track at same position as source
        track_item = HieroTrackItem.add_item_to_track(track, clip, timeline_in)

        if track_item:
            # Set metadata for tracking
            HieroTrackItem.set_metadata(track_item, "render_pass", render_pass.name)
            HieroTrackItem.set_metadata(track_item, "source_pattern", pattern)
            HieroTrackItem.set_metadata(
                track_item, "frame_range",
                f"{render_pass.start_frame}-{render_pass.end_frame}"
            )

        return track_item


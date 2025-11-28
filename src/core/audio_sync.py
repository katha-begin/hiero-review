"""
Audio Synchronizer Module
==========================
Audio track creation and synchronization with video shots.
"""
import re
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field

from .hiero_wrapper import HieroTimeline, HieroClip, HieroTrackItem, HIERO_AVAILABLE
from ..utils.path_parser import extract_episode, extract_sequence, extract_shot


# Audio file extensions
AUDIO_EXTENSIONS = {'.wav', '.mp3', '.aac', '.aiff', '.flac'}


@dataclass
class AudioMatch:
    """Represents an audio file matched to a video shot."""
    video_shot: str
    audio_path: str
    confidence: float  # 0.0 to 1.0


@dataclass
class SyncResult:
    """Result of audio synchronization."""
    success: bool
    matched_count: int = 0
    missing_audio: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class AudioSynchronizer:
    """
    Handles audio matching and synchronization with video timeline.
    """
    
    def __init__(
        self,
        audio_dir: str,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ):
        """
        Initialize AudioSynchronizer.
        
        Args:
            audio_dir: Directory containing audio files
            progress_callback: Optional callback(message, current, total)
        """
        self._audio_dir = Path(audio_dir)
        self._progress_callback = progress_callback
        self._audio_cache: Dict[str, List[str]] = {}
    
    def _report_progress(self, message: str, current: int = 0, total: int = 0) -> None:
        if self._progress_callback:
            self._progress_callback(message, current, total)
    
    def _scan_audio_files(self) -> List[str]:
        """Scan audio directory for audio files."""
        if not self._audio_dir.exists():
            return []
        
        audio_files = []
        for ext in AUDIO_EXTENSIONS:
            audio_files.extend(self._audio_dir.rglob(f"*{ext}"))
        
        return [str(f) for f in audio_files]
    
    def find_audio_for_shot(self, shot_info: Dict[str, str]) -> Optional[str]:
        """
        Find matching audio file for a shot.
        
        Args:
            shot_info: Dict with 'episode', 'sequence', 'shot' keys
            
        Returns:
            Path to matching audio file or None
        """
        ep = shot_info.get('episode', '')
        seq = shot_info.get('sequence', '')
        shot = shot_info.get('shot', '')
        
        if not self._audio_cache:
            self._audio_cache['files'] = self._scan_audio_files()
        
        audio_files = self._audio_cache.get('files', [])
        
        # Try exact match first
        for audio_path in audio_files:
            audio_name = Path(audio_path).stem.lower()
            if ep.lower() in audio_name and shot.lower() in audio_name:
                return audio_path
        
        # Try episode + shot match
        for audio_path in audio_files:
            audio_name = Path(audio_path).stem.lower()
            audio_ep = extract_episode(audio_name)
            audio_shot = extract_shot(audio_name)
            
            if audio_ep and audio_shot:
                if audio_ep.lower() == ep.lower() and audio_shot.lower() == shot.lower():
                    return audio_path
        
        return None
    
    def create_audio_track(
        self, sequence: Any, video_track: Any, shot_info_list: List[Dict]
    ) -> Tuple[Any, SyncResult]:
        """
        Create and populate audio track synced to video.
        
        Args:
            sequence: Hiero sequence
            video_track: Video track to sync with
            shot_info_list: List of shot info dicts with timeline positions
            
        Returns:
            Tuple of (audio_track, SyncResult)
        """
        result = SyncResult(success=True)
        
        # Create audio track
        audio_track = HieroTimeline.add_audio_track(sequence, "Audio")
        
        video_items = video_track.items() if hasattr(video_track, 'items') else []
        total = len(video_items)
        
        self._report_progress("Syncing audio", 0, total)
        
        for i, (video_item, shot_info) in enumerate(zip(video_items, shot_info_list)):
            # Find audio for this shot
            audio_path = self.find_audio_for_shot(shot_info)
            
            if not audio_path:
                result.missing_audio.append(shot_info.get('shot', f'Item {i}'))
                continue
            
            try:
                # Get video item timing
                if HIERO_AVAILABLE:
                    timeline_in = video_item.timelineIn()
                    timeline_out = video_item.timelineOut()
                else:
                    timeline_in = video_item.timeline_in
                    timeline_out = video_item.timeline_out
                
                # Create audio clip and add to track
                audio_clip = HieroClip.create_clip(audio_path)
                HieroTrackItem.add_item_to_track(
                    audio_track, audio_clip, timeline_in, timeline_out
                )
                result.matched_count += 1
                
            except Exception as e:
                result.errors.append(f"Shot {shot_info.get('shot', i)}: {str(e)}")
            
            self._report_progress(f"Synced {i+1}/{total}", i + 1, total)
        
        result.success = len(result.errors) == 0
        return audio_track, result
    
    def validate_audio_sync(self, audio_item: Any, video_item: Any) -> bool:
        """Check if audio and video items are properly synced."""
        try:
            if HIERO_AVAILABLE:
                return (audio_item.timelineIn() == video_item.timelineIn() and
                        audio_item.timelineOut() == video_item.timelineOut())
            else:
                return (audio_item.timeline_in == video_item.timeline_in and
                        audio_item.timeline_out == video_item.timeline_out)
        except Exception:
            return False


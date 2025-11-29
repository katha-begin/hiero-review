"""
Hiero API Wrapper Module
=========================
Abstraction layer for Hiero API operations.
Provides simplified interface and mock support for testing.
"""
from typing import Optional, List, Any, Tuple
from dataclasses import dataclass

# Try to import Hiero, fall back to mock if not available
try:
    import hiero.core
    import hiero.ui
    HIERO_AVAILABLE = True
except ImportError:
    HIERO_AVAILABLE = False


@dataclass
class ClipInfo:
    """Information about a clip."""
    path: str
    duration: int
    frame_rate: float
    start_frame: int = 0
    end_frame: int = 0


class HieroProject:
    """Wrapper for Hiero project operations."""
    
    @staticmethod
    def create_project(name: str) -> Any:
        """Create a new Hiero project."""
        if not HIERO_AVAILABLE:
            return MockProject(name)
        project = hiero.core.newProject()
        project.setName(name)
        return project
    
    @staticmethod
    def get_active_project() -> Any:
        """Get the currently active project."""
        if not HIERO_AVAILABLE:
            return MockProject("MockProject")
        projects = hiero.core.projects()
        return projects[0] if projects else None
    
    @staticmethod
    def create_bin(name: str, parent: Any = None) -> Any:
        """Create a bin in the project."""
        if not HIERO_AVAILABLE:
            return MockBin(name)
        project = parent or HieroProject.get_active_project()
        if project:
            clips_bin = project.clipsBin()
            return clips_bin.addItem(hiero.core.Bin(name))
        return None


class HieroTimeline:
    """Wrapper for Hiero timeline/sequence operations."""
    
    @staticmethod
    def create_sequence(name: str, fps: float = 24.0) -> Any:
        """Create a new sequence."""
        if not HIERO_AVAILABLE:
            return MockSequence(name, fps)
        project = HieroProject.get_active_project()
        if project:
            sequence = hiero.core.Sequence(name)
            sequence.setFramerate(fps)
            project.clipsBin().addItem(hiero.core.BinItem(sequence))
            return sequence
        return None
    
    @staticmethod
    def add_video_track(sequence: Any, name: str = "Video") -> Any:
        """Add a video track to sequence."""
        if not HIERO_AVAILABLE:
            return MockTrack(name, "video")
        return sequence.addTrack(hiero.core.VideoTrack(name))
    
    @staticmethod
    def add_audio_track(sequence: Any, name: str = "Audio") -> Any:
        """Add an audio track to sequence."""
        if not HIERO_AVAILABLE:
            return MockTrack(name, "audio")
        return sequence.addTrack(hiero.core.AudioTrack(name))
    
    @staticmethod
    def get_sequence_by_name(name: str) -> Any:
        """Find sequence by name in active project."""
        if not HIERO_AVAILABLE:
            return None
        project = HieroProject.get_active_project()
        if project:
            for item in project.clipsBin().items():
                if hasattr(item, 'activeItem'):
                    seq = item.activeItem()
                    if isinstance(seq, hiero.core.Sequence) and seq.name() == name:
                        return seq
        return None


class HieroClip:
    """Wrapper for Hiero clip operations."""

    @staticmethod
    def create_clip(media_path: str, add_to_bin: bool = True, bin_name: str = None) -> Any:
        """
        Create a clip from media file and optionally add to bin.

        Args:
            media_path: Path to media file (MOV or image sequence pattern)
            add_to_bin: Whether to add clip to project bin
            bin_name: Optional bin name (creates if not exists)

        Returns:
            Clip object
        """
        if not HIERO_AVAILABLE:
            return MockClip(media_path)

        # Create media source and clip
        source = hiero.core.MediaSource(media_path)
        clip = hiero.core.Clip(source)

        # Add to bin if requested
        if add_to_bin:
            project = HieroProject.get_active_project()
            if project:
                if bin_name:
                    # Find or create named bin
                    target_bin = HieroClip._get_or_create_bin(project, bin_name)
                else:
                    target_bin = project.clipsBin()

                # Add clip to bin
                bin_item = hiero.core.BinItem(clip)
                target_bin.addItem(bin_item)

        return clip

    @staticmethod
    def _get_or_create_bin(project: Any, bin_name: str) -> Any:
        """Find existing bin or create new one."""
        if not HIERO_AVAILABLE:
            return MockBin(bin_name)

        clips_bin = project.clipsBin()

        # Search for existing bin
        for item in clips_bin.items():
            if hasattr(item, 'name') and item.name() == bin_name:
                return item

        # Create new bin
        new_bin = hiero.core.Bin(bin_name)
        clips_bin.addItem(new_bin)
        return new_bin

    @staticmethod
    def create_from_sequence(pattern: str, frame_range: Tuple[int, int], add_to_bin: bool = True) -> Any:
        """Create a clip from image sequence."""
        if not HIERO_AVAILABLE:
            return MockClip(pattern, frame_range)
        # Pattern like: /path/to/file.%04d.exr
        source = hiero.core.MediaSource(pattern)
        clip = hiero.core.Clip(source)

        if add_to_bin:
            project = HieroProject.get_active_project()
            if project:
                bin_item = hiero.core.BinItem(clip)
                project.clipsBin().addItem(bin_item)

        return clip
    
    @staticmethod
    def get_duration(clip: Any) -> int:
        """Get clip duration in frames."""
        if not HIERO_AVAILABLE:
            return getattr(clip, 'duration', 100)
        return clip.duration()
    
    @staticmethod
    def get_frame_rate(clip: Any) -> float:
        """Get clip frame rate."""
        if not HIERO_AVAILABLE:
            return getattr(clip, 'fps', 24.0)
        return clip.framerate().toFloat()


class HieroTrackItem:
    """Wrapper for Hiero track item operations."""

    @staticmethod
    def add_item_to_track(track: Any, clip: Any, timeline_in: int, timeline_out: int) -> Any:
        """
        Add a clip to track at specified position.

        Per Hiero API:
        1. Create TrackItem with name and type
        2. Set source clip
        3. Set timeline in/out points
        4. Add to track
        """
        if not HIERO_AVAILABLE:
            return MockTrackItem(clip, timeline_in, timeline_out)

        # Get clip name for track item
        clip_name = "clip"
        try:
            if hasattr(clip, 'name'):
                clip_name = clip.name()
            elif hasattr(clip, 'mediaSource'):
                source = clip.mediaSource()
                if source:
                    clip_name = source.filename().split('/')[-1].split('\\')[-1]
        except:
            pass

        # Determine track type (video or audio)
        track_type = hiero.core.TrackItem.kVideo
        if hasattr(track, 'isAudioTrack') and track.isAudioTrack():
            track_type = hiero.core.TrackItem.kAudio

        # Create track item
        track_item = hiero.core.TrackItem(clip_name, track_type)

        # Set source clip
        track_item.setSource(clip)

        # Set timeline position
        track_item.setTimelineIn(timeline_in)
        track_item.setTimelineOut(timeline_out)

        # Add to track
        track.addItem(track_item)

        return track_item
    
    @staticmethod
    def update_item_source(item: Any, new_clip: Any) -> bool:
        """Update track item's source clip."""
        if not HIERO_AVAILABLE:
            item.clip = new_clip
            return True
        try:
            item.setSource(new_clip)
            return True
        except Exception:
            return False
    
    @staticmethod
    def add_tag(item: Any, tag_name: str, color: str = "red") -> Any:
        """Add a tag to track item."""
        if not HIERO_AVAILABLE:
            return MockTag(tag_name, color)
        tag = hiero.core.Tag(tag_name)
        item.addTag(tag)
        return tag
    
    @staticmethod
    def set_metadata(item: Any, key: str, value: str) -> bool:
        """Set metadata on track item."""
        if not HIERO_AVAILABLE:
            return True
        try:
            item.metadata().setValue(key, value)
            return True
        except Exception:
            return False


# ============================================================================
# Mock classes for testing outside Hiero
# ============================================================================

class MockProject:
    """Mock Hiero project for testing."""
    def __init__(self, name: str):
        self._name = name
        self._bins = []

    def name(self) -> str:
        return self._name

    def setName(self, name: str) -> None:
        self._name = name

    def clipsBin(self) -> 'MockBin':
        if not self._bins:
            self._bins.append(MockBin("Clips"))
        return self._bins[0]


class MockBin:
    """Mock Hiero bin for testing."""
    def __init__(self, name: str):
        self._name = name
        self._items = []

    def name(self) -> str:
        return self._name

    def addItem(self, item: Any) -> Any:
        self._items.append(item)
        return item

    def items(self) -> List[Any]:
        return self._items


class MockSequence:
    """Mock Hiero sequence for testing."""
    def __init__(self, name: str, fps: float = 24.0):
        self._name = name
        self._fps = fps
        self._tracks = []

    def name(self) -> str:
        return self._name

    def framerate(self) -> float:
        return self._fps

    def setFramerate(self, fps: float) -> None:
        self._fps = fps

    def addTrack(self, track: Any) -> Any:
        self._tracks.append(track)
        return track

    def videoTracks(self) -> List[Any]:
        return [t for t in self._tracks if t.track_type == "video"]

    def audioTracks(self) -> List[Any]:
        return [t for t in self._tracks if t.track_type == "audio"]


class MockTrack:
    """Mock Hiero track for testing."""
    def __init__(self, name: str, track_type: str = "video"):
        self._name = name
        self.track_type = track_type
        self._items = []

    def name(self) -> str:
        return self._name

    def addItem(self, clip: Any, timeline_in: int) -> 'MockTrackItem':
        item = MockTrackItem(clip, timeline_in, timeline_in + 100)
        self._items.append(item)
        return item

    def items(self) -> List[Any]:
        return self._items


class MockClip:
    """Mock Hiero clip for testing."""
    def __init__(self, path: str, frame_range: Tuple[int, int] = None):
        self._path = path
        self.duration = 100
        self.fps = 24.0
        if frame_range:
            self.duration = frame_range[1] - frame_range[0] + 1

    def mediaSource(self) -> 'MockMediaSource':
        return MockMediaSource(self._path)


class MockMediaSource:
    """Mock media source."""
    def __init__(self, path: str):
        self._path = path

    def fileinfos(self) -> List[Any]:
        return [self]

    def filename(self) -> str:
        return self._path


class MockTrackItem:
    """Mock Hiero track item for testing."""
    def __init__(self, clip: Any, timeline_in: int, timeline_out: int):
        self.clip = clip
        self.timeline_in = timeline_in
        self.timeline_out = timeline_out
        self._tags = []
        self._metadata = {}

    def source(self) -> Any:
        return self.clip

    def setSource(self, clip: Any) -> None:
        self.clip = clip

    def timelineIn(self) -> int:
        return self.timeline_in

    def timelineOut(self) -> int:
        return self.timeline_out

    def addTag(self, tag: Any) -> None:
        self._tags.append(tag)

    def tags(self) -> List[Any]:
        return self._tags


class MockTag:
    """Mock Hiero tag for testing."""
    def __init__(self, name: str, color: str = "red"):
        self._name = name
        self._color = color

    def name(self) -> str:
        return self._name


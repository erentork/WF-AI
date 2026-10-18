"""Push-to-talk microphone recorder. Audio lives only in RAM (WAV bytes)."""
import io
import wave


class MicRecorder:
    def __init__(self, samplerate: int = 16000, max_seconds: int = 30):
        self.samplerate = samplerate
        self.max_frames = samplerate * max_seconds
        self._stream = None
        self._chunks = []
        self._count = 0
        try:
            import sounddevice as sd  # noqa: WPS433
            self._sd = sd
        except Exception:
            self._sd = None

    @property
    def available(self) -> bool:
        return self._sd is not None

    def start(self) -> None:
        if not self._sd or self._stream is not None:
            return
        self._chunks = []
        self._count = 0

        def callback(indata, frames, _time, _status):
            if self._count < self.max_frames:
                self._chunks.append(indata.copy())
                self._count += frames

        try:
            self._stream = self._sd.InputStream(
                samplerate=self.samplerate, channels=1, dtype="int16", callback=callback
            )
            self._stream.start()
        except Exception:
            self._stream = None

    def stop(self, keep: bool):
        """Stops recording. Returns WAV bytes if keep=True and enough audio, else None."""
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        chunks, self._chunks = self._chunks, []
        if not keep or not chunks:
            return None

        pcm = b"".join(c.tobytes() for c in chunks)
        del chunks
        if len(pcm) < self.samplerate * 2 * 0.3:  # < 0.3s of audio
            return None

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.samplerate)
            wf.writeframes(pcm)
        data = buf.getvalue()
        buf.close()
        return data

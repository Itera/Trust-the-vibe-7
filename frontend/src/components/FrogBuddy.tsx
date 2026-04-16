import { useEffect, useRef, useState } from "react";
import { fetchFrogMessage } from "../api";
import { playFrogCroak } from "../frogSound";

interface FrogBuddyProps {
  task?: string;
}

export default function FrogBuddy({ task }: FrogBuddyProps) {
  const [clickCount, setClickCount] = useState(0);
  const [growthClicks, setGrowthClicks] = useState(0);
  const [message, setMessage] = useState<string | null>(null);
  const [annoyed, setAnnoyed] = useState(false);
  const [jumping, setJumping] = useState(false);
  const [raging, setRaging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [visible, setVisible] = useState(false);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isHovering = useRef(false);

  const frogScale = 1 + growthClicks * 0.1;

  const scheduleHide = (delay: number) => {
    if (hideTimer.current) clearTimeout(hideTimer.current);
    hideTimer.current = setTimeout(() => setVisible(false), delay);
  };

  const handleMouseEnter = () => {
    isHovering.current = true;
    if (hideTimer.current) {
      clearTimeout(hideTimer.current);
      hideTimer.current = null;
    }
  };

  const handleMouseLeave = () => {
    isHovering.current = false;
    if (visible) scheduleHide(3000);
  };

  const handleClick = async () => {
    if (loading) return;

    const nextCount = clickCount + 1;
    setClickCount(nextCount);
    setLoading(true);
    setVisible(false);

    // Play croak immediately on click — pitch rises with each growth step
    playFrogCroak(1 + growthClicks * 0.08);

    if (hideTimer.current) {
      clearTimeout(hideTimer.current);
      hideTimer.current = null;
    }

    try {
      const data = await fetchFrogMessage(nextCount, task?.trim() || undefined);
      setMessage(data.message);
      setAnnoyed(data.annoyed);
      setVisible(true);
      if (data.annoyed) {
        setGrowthClicks(0);
        setRaging(true);
        playFrogCroak(0.35, true); // scary low croak on rage
      } else {
        setGrowthClicks((n) => n + 1);
        setJumping(true);
      }
      if (!isHovering.current) scheduleHide(3000);
    } catch {
      setMessage("*ribbit* — something went wrong.");
      setAnnoyed(false);
      setVisible(true);
      if (!isHovering.current) scheduleHide(3000);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    return () => {
      if (hideTimer.current) clearTimeout(hideTimer.current);
    };
  }, []);

  return (
    <div
      className="frog-buddy"
      aria-label="Frog buddy"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {visible && message && (
        <div className={`frog-bubble${annoyed ? " frog-bubble--annoyed" : ""}`}>
          {message}
        </div>
      )}
      <div
        className={raging ? "frog-scale frog-scale--raging" : "frog-scale"}
        style={{ transform: `scale(${frogScale})`, transformOrigin: "bottom right", transition: "transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)" }}
        onAnimationEnd={() => setRaging(false)}
      >
        <button
          className={`frog-btn${loading ? " frog-btn--loading" : ""}${jumping ? " frog-btn--jumping" : ""}${annoyed && visible ? " frog-btn--annoyed" : ""}`}
          onClick={handleClick}
          onAnimationEnd={() => setJumping(false)}
          aria-label="Click the frog for motivation"
          title="Click me!"
        >
          {loading ? "⏳" : "🐸"}
        </button>
      </div>
    </div>
  );
}

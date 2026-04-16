import type { Card } from "../types";

interface Props {
  card: Card;
}

const SIZE_BY_KIND: Record<string, string> = {
  peptalk: "card--hero",
  video: "card--video",
  mood_board: "card--mood",
  image: "card--tall",
  fact: "card--wide",
  quote: "card--wide",
  haiku: "card--tall",
  playlist: "card--wide",
};

function CardHeader({ card }: { card: Card }) {
  return (
    <header className="card__header">
      <span className="card__kind">{card.kind.replace("_", " ")}</span>
      {card.source && <span className="card__source">{card.source}</span>}
    </header>
  );
}

function VideoBody({ card }: { card: Card }) {
  if (!card.video_url) {
    return <p className="card__body">{card.body}</p>;
  }
  return (
    <div className="card__video">
      <video
        src={card.video_url}
        poster={card.video_poster ?? undefined}
        controls
        muted
        loop
        playsInline
        preload="metadata"
      />
      {card.body && <p className="card__body card__body--caption">{card.body}</p>}
    </div>
  );
}

function MoodBoardBody({ card }: { card: Card }) {
  const urls = card.image_urls ?? [];
  if (urls.length === 0) {
    return <p className="card__body">{card.body}</p>;
  }
  return (
    <div className="card__mood">
      <div className="card__mood-grid">
        {urls.slice(0, 4).map((url, i) => (
          <img key={url + i} src={url} alt="" loading="lazy" />
        ))}
      </div>
      {card.body && <p className="card__body card__body--caption">{card.body}</p>}
    </div>
  );
}

function DefaultBody({ card }: { card: Card }) {
  if (card.image_url) {
    return (
      <figure className="card__figure">
        <img src={card.image_url} alt="" loading="lazy" />
        {card.body && <figcaption>{card.body}</figcaption>}
      </figure>
    );
  }
  return <p className="card__body">{card.body}</p>;
}

export default function MotivationCard({ card }: Props) {
  const sizeClass = SIZE_BY_KIND[card.kind] ?? "card--small";

  return (
    <article className={`card card--${card.kind} ${sizeClass}`}>
      <CardHeader card={card} />
      <h3 className="card__title">{card.title}</h3>

      {card.kind === "video" ? (
        <VideoBody card={card} />
      ) : card.kind === "mood_board" ? (
        <MoodBoardBody card={card} />
      ) : (
        <DefaultBody card={card} />
      )}

      {card.attribution && (
        <footer className="card__attribution">{card.attribution}</footer>
      )}
    </article>
  );
}

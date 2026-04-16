import type { Card } from "../types";

interface Props {
  card: Card;
}

const SIZE_BY_KIND: Record<string, string> = {
  peptalk: "card--hero",
  image: "card--tall",
  fact: "card--wide",
  quote: "card--wide",
  haiku: "card--tall",
  playlist: "card--wide",
};

export default function MotivationCard({ card }: Props) {
  const sizeClass = SIZE_BY_KIND[card.kind] ?? "card--small";

  return (
    <article className={`card card--${card.kind} ${sizeClass}`}>
      <header className="card__header">
        <span className="card__kind">{card.kind.replace("_", " ")}</span>
        {card.source && <span className="card__source">{card.source}</span>}
      </header>

      <h3 className="card__title">{card.title}</h3>

      {card.image_url ? (
        <figure className="card__figure">
          <img src={card.image_url} alt="" loading="lazy" />
          {card.body && <figcaption>{card.body}</figcaption>}
        </figure>
      ) : (
        <p className="card__body">{card.body}</p>
      )}

      {card.attribution && (
        <footer className="card__attribution">{card.attribution}</footer>
      )}
    </article>
  );
}

import { Instagram } from "lucide-react";

export default function Footer() {
  return (
    <footer>
      <div className="brand">
        <img src="/footer-logo.svg" alt="Treats & Temptation by SK" className="brand-logo footer-logo" />
      </div>
      <span>Made with butter, time & a little bit of magic.</span>
      <a href="https://www.instagram.com/treatsandtemptationbysk/" target="_blank" rel="noreferrer" data-testid="footer-instagram">
        @treatsandtemptationbysk <Instagram size={16} />
      </a>
    </footer>
  );
}

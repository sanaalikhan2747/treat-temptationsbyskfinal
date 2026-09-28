import { Instagram } from "lucide-react";

export default function Footer() {
  return (
    <footer>
      <div className="brand">
        <span className="brand-mark">SK</span>
        <span>Treats &<br /><b>Temptation</b></span>
      </div>
      <span>Made with butter, time & a little bit of magic.</span>
      <a href="https://www.instagram.com/treatsandtemptationbysk/" target="_blank" rel="noreferrer" data-testid="footer-instagram">
        @treatsandtemptationbysk <Instagram size={16} />
      </a>
    </footer>
  );
}

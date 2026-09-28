import axios from "axios";

export const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
export const WHATSAPP_PHONE = "923224112832"; // +92 322 4112832

export const api = axios.create({ baseURL: API });

export function waLink(text) {
  return `https://wa.me/${WHATSAPP_PHONE}?text=${encodeURIComponent(text)}`;
}

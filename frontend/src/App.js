import { useState } from "react";
import { Routes, Route } from "react-router-dom";
import "@/App.css";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import CartDrawer from "@/components/CartDrawer";
import ChatDrawer from "@/components/ChatDrawer";
import Home from "@/pages/Home";
import Menu from "@/pages/Menu";
import BuildBox from "@/pages/BuildBox";
import FestiveBoxEditor from "@/pages/FestiveBoxEditor";
import Checkout from "@/pages/Checkout";
import OrderSuccess from "@/pages/OrderSuccess";

export default function App() {
  const [chatOpen, setChatOpen] = useState(false);
  return (
    <div className="site-shell">
      <Nav onOpenChat={() => setChatOpen(true)} />
      <main id="top">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/menu" element={<Menu />} />
          <Route path="/build" element={<BuildBox />} />
          <Route path="/festive/:boxId" element={<FestiveBoxEditor />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/order/:orderNumber" element={<OrderSuccess />} />
        </Routes>
      </main>
      <Footer />
      <CartDrawer />
      <ChatDrawer open={chatOpen} onClose={() => setChatOpen(false)} />
    </div>
  );
}

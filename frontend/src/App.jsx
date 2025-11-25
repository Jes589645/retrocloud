import { useState } from "react";
import Login from "./pages/Login";
import Games from "./pages/Games";

export default function App() {
  const [loggedIn, setLoggedIn] = useState(false);

  if (!loggedIn) {
    return <Login onLoggedIn={() => setLoggedIn(true)} />;
  }
  return <Games />;
}

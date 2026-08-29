import { useState } from "react";

import AIChatButton from "./AIChatButton";
import AIChatWindow from "./AIChatWindow";

export default function AIChatbot() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <AIChatWindow
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
      />

      <AIChatButton
        isOpen={isOpen}
        onClick={() =>
          setIsOpen((current) => !current)
        }
      />
    </>
  );
}
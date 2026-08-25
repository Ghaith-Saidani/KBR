import HeroSection from "../components/home/HeroSection";
import AboutSection from "../components/home/AboutSection";
import FocusSection from "../components/home/FocusSection";
import EventsPreview from "../components/home/EventsPreview";
import NewsPreview from "../components/home/NewsPreview";
import JoinSection from "../components/home/JoinSection";

export default function HomePage() {
  return (
    <>
      <HeroSection />
      <AboutSection />
      <FocusSection />
      <EventsPreview />
      <NewsPreview />
      <JoinSection />
    </>
  );
}

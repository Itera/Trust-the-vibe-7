import { useState } from "react";
import Motivator from "./components/Motivator";
import FrogBuddy from "./components/FrogBuddy";
import "./app.css";

export default function App() {
  const [task, setTask] = useState("");
  return (
    <>
      <Motivator task={task} onTaskChange={setTask} />
      <FrogBuddy task={task} />
    </>
  );
}

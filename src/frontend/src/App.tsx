// import { useState } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from './assets/vite.svg'
// import heroImg from './assets/hero.png'
// import './App.css'

// function App() {
//   const [count, setCount] = useState(0)

//   return (
//     <>
//       <section id="center">
//         <div className="hero">
//           <img src={heroImg} className="base" width="170" height="179" alt="" />
//           <img src={reactLogo} className="framework" alt="React logo" />
//           <img src={viteLogo} className="vite" alt="Vite logo" />
//         </div>
//         <div>
//           <h1>Get started</h1>
//           <p>
//             Edit <code>src/App.tsx</code> and save to test <code>HMR</code>
//           </p>
//         </div>
//         <button
//           type="button"
//           className="counter"
//           onClick={() => setCount((count) => count + 1)}
//         >
//           Count is {count}
//         </button>
//       </section>

//       <div className="ticks"></div>

//       <section id="next-steps">
//         <div id="docs">
//           <svg className="icon" role="presentation" aria-hidden="true">
//             <use href="/icons.svg#documentation-icon"></use>
//           </svg>
//           <h2>Documentation</h2>
//           <p>Your questions, answered</p>
//           <ul>
//             <li>
//               <a href="https://vite.dev/" target="_blank">
//                 <img className="logo" src={viteLogo} alt="" />
//                 Explore Vite
//               </a>
//             </li>
//             <li>
//               <a href="https://react.dev/" target="_blank">
//                 <img className="button-icon" src={reactLogo} alt="" />
//                 Learn more
//               </a>
//             </li>
//           </ul>
//         </div>
//         <div id="social">
//           <svg className="icon" role="presentation" aria-hidden="true">
//             <use href="/icons.svg#social-icon"></use>
//           </svg>
//           <h2>Connect with us</h2>
//           <p>Join the Vite community</p>
//           <ul>
//             <li>
//               <a href="https://github.com/vitejs/vite" target="_blank">
//                 <svg
//                   className="button-icon"
//                   role="presentation"
//                   aria-hidden="true"
//                 >
//                   <use href="/icons.svg#github-icon"></use>
//                 </svg>
//                 GitHub
//               </a>
//             </li>
//             <li>
//               <a href="https://chat.vite.dev/" target="_blank">
//                 <svg
//                   className="button-icon"
//                   role="presentation"
//                   aria-hidden="true"
//                 >
//                   <use href="/icons.svg#discord-icon"></use>
//                 </svg>
//                 Discord
//               </a>
//             </li>
//             <li>
//               <a href="https://x.com/vite_js" target="_blank">
//                 <svg
//                   className="button-icon"
//                   role="presentation"
//                   aria-hidden="true"
//                 >
//                   <use href="/icons.svg#x-icon"></use>
//                 </svg>
//                 X.com
//               </a>
//             </li>
//             <li>
//               <a href="https://bsky.app/profile/vite.dev" target="_blank">
//                 <svg
//                   className="button-icon"
//                   role="presentation"
//                   aria-hidden="true"
//                 >
//                   <use href="/icons.svg#bluesky-icon"></use>
//                 </svg>
//                 Bluesky
//               </a>
//             </li>
//           </ul>
//         </div>
//       </section>

//       <div className="ticks"></div>
//       <section id="spacer"></section>
//     </>
//   )
// }

// export default App
// function App() {
//   return (
//     <main>
//       <h1>hello world</h1>
//     </main>
//   );
// }

// export default App;
import { useEffect, useState } from "react";

type Appointment = {
  id: number;
  studentName: string;
  matriculationNumber: string;
  studyProgram: string;
  date: string;
  time: string;
  studyPlanStatus: "Uploaded" | "Missing";
  transcriptStatus: "Uploaded" | "Missing";
  minutesStatus: "Not uploaded" | "Uploaded";
};

const appointments: Appointment[] = [
  {
    id: 1,
    studentName: "Max Müller",
    matriculationNumber: "123456",
    studyProgram: "Computer Science",
    date: "15.10.2026",
    time: "10:00 - 10:30",
    studyPlanStatus: "Uploaded",
    transcriptStatus: "Uploaded",
    minutesStatus: "Not uploaded",
  },
  {
    id: 2,
    studentName: "Anna Weber",
    matriculationNumber: "654321",
    studyProgram: "Information Systems",
    date: "15.10.2026",
    time: "10:30 - 11:00",
    studyPlanStatus: "Missing",
    transcriptStatus: "Missing",
    minutesStatus: "Not uploaded",
  },
];

function CounselorDashboard() {
  const [echoData, setEchoData] = useState<string | null>(null);
  const [echoError, setEchoError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/counselors/echo-data/")
      .then((res) => res.json())
      .then((data) => setEchoData(JSON.stringify(data)))
      .catch((err) => setEchoError(String(err)));
  }, []);

  return (
    <main>
      <h1>Counselor Dashboard</h1>
      <p>Here you can see your assigned counseling appointments.</p>

      <p>
        <strong>Backend connection check:</strong>{" "}
        {echoError
          ? `Error: ${echoError}`
          : echoData !== null
            ? echoData
            : "Loading…"}
      </p>

      <table border={1} cellPadding={8}>
        <thead>
          <tr>
            <th>Student</th>
            <th>Study Program</th>
            <th>Date</th>
            <th>Time</th>
            <th>Study Plan</th>
            <th>Transcript</th>
            <th>Minutes</th>
          </tr>
        </thead>

        <tbody>
          {appointments.map((appointment) => (
            <tr key={appointment.id}>
              <td>{appointment.studentName}</td>
              <td>{appointment.studyProgram}</td>
              <td>{appointment.date}</td>
              <td>{appointment.time}</td>
              <td>{appointment.studyPlanStatus}</td>
              <td>{appointment.transcriptStatus}</td>
              <td>{appointment.minutesStatus}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}

function App() {
  return <CounselorDashboard />;
}

export default App;

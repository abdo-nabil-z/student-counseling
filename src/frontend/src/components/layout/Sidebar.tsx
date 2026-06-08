import { Link } from "react-router-dom";

function Sidebar() {
  return (
    <aside className="sidebar">
      <h2>Study Counseling</h2>

      <nav>
        <Link to="/">Dashboard</Link>
        <Link to="/students/import">Import Students</Link>
        <Link to="/students">Students</Link>
        <Link to="/counselors">Counselors</Link>
        <Link to="/slots">Time Slots</Link>
        <Link to="/planning">Planning</Link>
        {/* <Link to="/student-mail">Student Mail</Link> */}
        <Link to="/counselor-mail">Sessions</Link>
        <Link to="/documents">Documents</Link>
        <Link to="/minutes">Minutes</Link>
        <Link to="/no-shows">No-Shows</Link>
        {/* <Link to="/final-bundle">Final Bundle</Link> */}
      </nav>
    </aside>
  );
}

export default Sidebar;

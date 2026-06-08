function PlanningPage() {
  return (
    <section>
      <h2>Counseling Planning</h2>

      <div className="card">
        <h3>Assign Student to Appointment</h3>

        <label>Student</label>
        <select>
          <option>Select student</option>
          <option>Peter - 123456</option>
        </select>

        <label>Counselor</label>
        <select>
          <option>Select counselor</option>
          <option>Prof. Dr. Thomas </option>
        </select>

        <label>Date</label>
        <input type="date" />

        <label>Time</label>
        <input type="time" />

        <label>Location</label>
        <input placeholder="Example: AE22-R273" />

        <label>
          <input type="checkbox" /> Send appointment email after assignment
        </label>

        <button>Assign Appointment</button>
      </div>
    </section>
  );
}

export default PlanningPage;

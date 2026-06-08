function SlotsPage() {
  return (
    <section>
      <h2>Time Slots</h2>

      <div className="card">
        <h3>Create Availability Block</h3>

        <label>Counselor</label>
        <select>
          <option>Select counselor</option>
          <option>Prof. Dr. Thomas </option>
        </select>

        <label>Date</label>
        <input type="date" />

        <label>Start Time</label>
        <input type="time" />

        <label>End Time</label>
        <input type="time" />

        {/* <button>Preview 30-minute Slots</button> */}
        <button>Create Slots</button>
      </div>

      {/* <div className="card">
        <h3>Example Slots</h3>
        <ul>
          <li>14:00 - 14:30</li>
          <li>14:30 - 15:00</li>
          <li>15:00 - 15:30</li>
        </ul>
      </div> */}
    </section>
  );
}

export default SlotsPage;

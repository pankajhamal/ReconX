import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";

const COLORS = ["#2a9d8f", "#e9c46a", "#e76f51", "#264653"];

export default function Charts({ summary }) {
  const matchedData = [
    { name: "Matched", value: summary.matched },
    { name: "Pending", value: summary.pending },
    { name: "Discrepancies", value: summary.discrepancies },
  ];

  const outcomeData = Object.entries(summary.by_payment_outcome).map(
    ([name, count]) => ({ name, count })
  );

  return (
    <div className="charts">
      <ChartBox title="Matched vs unmatched">
        <PieChart>
          <Pie data={matchedData} dataKey="value" nameKey="name" outerRadius={90} label>
            {matchedData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ChartBox>

      <ChartBox title="Payment outcomes">
        <BarChart data={outcomeData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" fontSize={11} />
          <YAxis />
          <Tooltip />
          <Bar dataKey="count" fill={COLORS[3]} />
        </BarChart>
      </ChartBox>
    </div>
  );
}

function ChartBox({ title, children }) {
  return (
    <div className="chart">
      <h3>{title}</h3>
      <ResponsiveContainer width="100%" height={260}>
        {children}
      </ResponsiveContainer>
    </div>
  );
}

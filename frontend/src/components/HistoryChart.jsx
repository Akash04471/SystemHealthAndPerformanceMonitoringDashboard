import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ 
        backgroundColor: "rgba(11, 17, 32, 0.95)", 
        border: "1px solid rgba(16, 185, 129, 0.3)", 
        padding: "14px", 
        borderRadius: "4px",
        backdropFilter: "blur(12px)",
        boxShadow: "0 20px 40px rgba(0,0,0,0.5)"
      }}>
        <p style={{ color: "#64748b", fontSize: "0.65rem", marginBottom: "10px", fontWeight: "800", textTransform: 'uppercase', letterSpacing: '0.1em' }}>{label}</p>
        {payload.map((entry, index) => (
          <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '1px', background: entry.color }}></div>
            <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', gap: '20px' }}>
              <span style={{ fontSize: "0.75rem", color: "#94a3b8", fontWeight: "500" }}>{entry.name}</span>
              <span style={{ fontSize: "0.75rem", color: "#fff", fontWeight: "700" }}>{entry.value.toFixed(1)}%</span>
            </div>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export function HistoryChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '350px' }}>
        <p style={{ color: "var(--text-muted)", fontSize: '0.85rem' }}>Awaiting historical telemetry data...</p>
      </div>
    );
  }

  const chartData = data.map((d) => ({
    time: new Date(d.hour).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    CPU: parseFloat(d.avg_cpu),
    Memory: parseFloat(d.avg_memory),
    Disk: parseFloat(d.avg_disk)
  }));

  return (
    <div style={{ width: "100%", height: 350, marginTop: "20px" }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorCPU" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorMem" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorDisk" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.03)" vertical={false} />
          <XAxis 
            dataKey="time" 
            stroke="#64748b" 
            fontSize={10} 
            tickLine={false} 
            axisLine={false}
            dy={10}
            interval="preserveStartEnd"
          />
          <YAxis 
            stroke="#64748b" 
            fontSize={10} 
            tickLine={false} 
            axisLine={false}
            domain={[0, 100]} 
          />
          <Tooltip 
            content={<CustomTooltip />} 
            cursor={{ stroke: 'rgba(148, 163, 184, 0.1)', strokeWidth: 2 }}
          />
          <Legend 
            verticalAlign="top" 
            align="right"
            wrapperStyle={{ fontSize: "9px", paddingBottom: "30px", textTransform: "uppercase", letterSpacing: "0.15em", fontWeight: 700 }} 
            iconType="rect"
            iconSize={8}
          />
          <Area 
            type="monotone" 
            dataKey="CPU" 
            stroke="#10b981" 
            fillOpacity={1} 
            fill="url(#colorCPU)" 
            strokeWidth={2}
            animationDuration={2000}
          />
          <Area 
            type="monotone" 
            dataKey="Memory" 
            stroke="#3b82f6" 
            fillOpacity={1} 
            fill="url(#colorMem)" 
            strokeWidth={2}
            animationDuration={2000}
          />
          <Area 
            type="monotone" 
            dataKey="Disk" 
            stroke="#f59e0b" 
            fillOpacity={1} 
            fill="url(#colorDisk)" 
            strokeWidth={2}
            animationDuration={2000}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

import { useEffect, useState, useCallback } from "react";
import Highcharts from "highcharts";
import HighchartsReact from "highcharts-react-official";
import { z } from "zod";

const bno055DataSchema = z.object({
  _timestamp: z.number(),
  _sensor: z.string(),
  _measurement: z.string(),
  _value: z.object({
    frequency: z.array(z.number()),
    x_axis: z.array(z.number()),
    y_axis: z.array(z.number()),
    z_axis: z.array(z.number()),
  }),
});

type Series = Array<{ name: string; data: number[] }>;

export const App = () => {
  const [series, setSeries] = useState<Series>([]);
  const [categories, setCategories] = useState<number[]>([]);
  const [title, setTitle] = useState("");
  const [liveData, setLiveData] = useState(true);

  const getBno055Data = useCallback(async (msSinceEpoch: number) => {
    const response = await fetch(
      `${window.location.protocol}//${window.location.hostname}:8000/bno055?ms_since_epoch=${msSinceEpoch}`
    );
    const jsonData = await response.json();
    const result = bno055DataSchema.safeParse(jsonData);
    if (result.success) {
      setCategories(result.data._value.frequency.map(Math.round));
      setSeries([
        { name: "X Axis", data: result.data._value.x_axis },
        { name: "Y Axis", data: result.data._value.y_axis },
        { name: "Z Axis", data: result.data._value.z_axis },
      ]);
      const timestamp = new Date(result.data._timestamp)
        .toISOString()
        .slice(0, -5);
      setTitle(
        `${result.data._sensor.toUpperCase()} Vibration Data (${timestamp})`
      );
    }
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      if (liveData) getBno055Data(new Date().getTime());
    }, 1000);
    return () => clearInterval(interval);
  }, [liveData]);

  return (
    <div>
      <HighchartsReact
        highcharts={Highcharts}
        options={{
          title: {
            text: title,
          },
          xAxis: { categories },
          series,
        }}
        updateArgs={[true, true, false]}
      />
      <div
        style={{
          display: "flex",
          width: "100%",
          justifyContent: "space-around",
        }}
      >
        <input
          type="datetime-local"
          defaultValue={new Date().toISOString().slice(0, -5)}
          onInput={(event: React.ChangeEvent<HTMLInputElement>) => {
            const nextTimestamp = new Date(event.target.value).getTime();
            setLiveData(false);
            getBno055Data(nextTimestamp);
          }}
        />
        <button type="button" onClick={() => setLiveData(!liveData)}>
          {liveData
            ? "Automatic fetching of newest data"
            : "Fetching by input time"}
        </button>
      </div>
    </div>
  );
};

import GaugeChart from "react-gauge-chart"

import { useTheme } from "@mui/material/styles"

export const Gauge = ({ data }: any) => {
  const theme = useTheme()

  return (
    <GaugeChart
      percent={data}
      id="gauge-chart2"
      textColor={theme.palette.mode === "dark" ? "yellow" : "#345243"}
    />
  )
}

import * as React from "react"

import Box from "@mui/material/Box"
import { useTheme } from "@mui/material/styles"

import Link from "@components/Link"

import LogoSVG from "../../public/logo.svg"

export const Logo = () => {
  const theme = useTheme()

  return (
    <Box href="/" component={Link}>
      <LogoSVG
        width={100}
        height={50}
        fill={
          theme.palette.mode === "dark"
            ? theme.palette.common.white
            : theme.palette.common.black
        }
      />
    </Box>
  )
}

import React from "react"
import Head from "next/head"
import type { NextPage } from "next"

import Box from "@mui/material/Box"
import Typography from "@mui/material/Typography"

import { APP_NAME } from "@utils/constants"
import { HeaderLayout } from "@layouts/Header"

const Home: NextPage = () => {
  return (
    <>
      <Head>
        <title>{APP_NAME}</title>
        <meta name="description" content={APP_NAME} />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <HeaderLayout>
        <Box
          sx={{
            py: 14,
            width: "100%",
            height: "100%",
            display: "flex",
            alignItems: "center",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          {/* Title */}
          <Typography align="center" variant="h2" sx={{ maxWidth: "sm" }}>
            Monitoring the system & user behaviour in Linux (debian)
          </Typography>

          {/* Info */}
          <Box>
            <Typography
              align="center"
              variant="h6"
              color="text.secondary"
              sx={{ maxWidth: "sm" }}
            >
              A project submitted to University of Hertfordshire, Department of
              Computer Science <br />
              in partial fulfilment of the requirements for the degree of <br />
              MASTER OF SCIENCE IN CYBER SECURITY
            </Typography>
          </Box>

          {/* Student */}
          <Box>
            <Typography
              align="center"
              variant="subtitle1"
              color="text.secondary"
            >
              by
            </Typography>

            <Typography variant="h4" align="center" color="text.secondary">
              MUHAMMAD AWAIS KHAN
            </Typography>
          </Box>

          {/* Supervisor */}
          <Box>
            <Typography align="center" variant="h6" color="text.secondary">
              Supervisor: Kufreh Sampson
            </Typography>
            <Typography align="center" variant="h6" color="text.secondary">
              September 2022
            </Typography>
          </Box>
        </Box>
      </HeaderLayout>
    </>
  )
}

export default Home

import Head from "next/head"
import { useRouter } from "next/router"
import { useState, useEffect } from "react"

import Box from "@mui/material/Box"
import Card from "@mui/material/Card"
import Grid from "@mui/material/Grid"
import Typography from "@mui/material/Typography"
import CardContent from "@mui/material/CardContent"
import CardActionArea from "@mui/material/CardActionArea"
import CircularProgress from "@mui/material/CircularProgress"

import { useApi } from "@hooks/useApi"
import { APP_NAME } from "@utils/constants"
import { Heading } from "@components/Title"
import { ENDPOINTS } from "@utils/constants"
import { DrawerLayout } from "@layouts/Drawer"

export default function Dashboard() {
  const [api] = useApi()
  const router = useRouter()

  const [clients, setClients] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // api call
    fetchClients()
    // eslint-disable-next-line
  }, [])

  const fetchClients = async () => {
    try {
      const response = await api({
        method: "GET",
        uri: ENDPOINTS.clients,
      })

      setClients(response?.clients)

      setLoading(false)
    } catch (err) {}
  }

  return (
    <>
      <Head>
        <title>Clients - {APP_NAME}</title>
      </Head>

      <DrawerLayout title="Clients">
        <Heading sx={{ mb: 1 }}>Clients</Heading>

        {loading ? (
          <Box
            sx={{
              width: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <CircularProgress />
          </Box>
        ) : (
          <Grid container spacing={4}>
            {clients.map((client: any) => {
              return (
                <Grid item key={client.id} xs={6} sm={4} lg={3}>
                  <Card variant="outlined">
                    <CardActionArea
                      onClick={() => {
                        if (typeof window !== "undefined" && client.id) {
                          router.push({
                            pathname: "/app/clients/[id]",
                            query: { id: client._id },
                          })
                        }
                      }}
                    >
                      <CardContent>
                        <Typography variant="h5" component="div">
                          {client.host_name}
                        </Typography>
                        <Typography
                          sx={{ mt: 1.5 }}
                          variant="subtitle2"
                          color="text.secondary"
                        >
                          IP: {client.ip}
                        </Typography>
                        <Typography variant="subtitle2" color="text.secondary">
                          Online Users: {client.user_count}
                        </Typography>
                      </CardContent>
                    </CardActionArea>
                  </Card>
                </Grid>
              )
            })}
          </Grid>
        )}
      </DrawerLayout>
    </>
  )
}

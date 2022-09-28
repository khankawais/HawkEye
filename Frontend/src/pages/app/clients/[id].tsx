import Head from "next/head"
import { useRouter } from "next/router"
import { useState, useEffect } from "react"
import ReactDiffViewer from "react-diff-viewer"

import { Box } from "@mui/material"
import { Card } from "@mui/material"
import { Grid } from "@mui/material"
import { Chip } from "@mui/material"
import { Stack } from "@mui/material"
import { Add } from "@mui/icons-material"
import { Tabs, Tab } from "@mui/material"
import { Typography } from "@mui/material"
import { CardContent } from "@mui/material"
import { Refresh } from "@mui/icons-material"
import { LinearProgress } from "@mui/material"
import { useTheme } from "@mui/material/styles"
import { Visibility } from "@mui/icons-material"
import { CircularProgress } from "@mui/material"

import { useApi } from "@hooks/useApi"
import { APP_NAME } from "@utils/constants"
import { Heading } from "@components/Title"
import { Dialog } from "@components/Dialog"
import { Button } from "@components/Button"
import { ENDPOINTS } from "@utils/constants"
import { DrawerLayout } from "@layouts/Drawer"
import { Gauge } from "@components/Graphs/Gauge"
import { DataTable } from "@components/DataTable"
import { IconButton } from "@components/IconButton"
import { EditStatus, CustomAlertSettings } from "@forms/alerts"

export default function ClientDetails() {
  const [api] = useApi()
  const router = useRouter()

  const [tab, setTab] = useState<number>(0)
  const [client, setClient] = useState<any>({})

  useEffect(() => {
    if (router.query.id) {
      fetchClient(router.query.id as string)
    }

    // eslint-disable-next-line
  }, [router.query])

  const fetchClient = async (id: string) => {
    try {
      const response = await api({
        method: "GET",
        uri: ENDPOINTS.clients,
      })

      setClient(response?.clients?.find((item: any) => item.id === id))
    } catch (err) {}
  }

  return (
    <>
      <Head>
        <title>Client Details - {APP_NAME}</title>
      </Head>

      <DrawerLayout
        title={`Client Details: ${client?.host_name || ""}`}
        withBackButton
      >
        <Box
          sx={{
            mb: 1,
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
          }}
        >
          <Tabs
            value={tab}
            sx={{ mr: 2 }}
            aria-label="client-tabs"
            onChange={(_: React.SyntheticEvent, value: number) => setTab(value)}
          >
            <Tab
              label="Stats"
              id={`client-tab-${0}`}
              aria-controls={`client-tab-${0}`}
            />
            <Tab
              label="Ports"
              id={`client-tab-${1}`}
              aria-controls={`client-tab-${1}`}
            />
            <Tab
              label="Processes"
              id={`client-tab-${2}`}
              aria-controls={`client-tab-${2}`}
            />
            <Tab
              label="Alerts"
              id={`client-tab-${3}`}
              aria-controls={`client-tab-${3}`}
            />
          </Tabs>

          <Dialog
            fullWidth
            maxWidth="sm"
            title="Alert Details"
            trigger={({ toggleOpen }: { toggleOpen: () => void }) => (
              <Button variant="text" startIcon={<Add />} onClick={toggleOpen}>
                Custom Alerts
              </Button>
            )}
            content={() => (
              <CustomAlertSettings clientId={router.query.id as string} />
            )}
          />
        </Box>

        {tab === 0 ? (
          <ClientStats details={client} />
        ) : tab === 1 ? (
          <ClientPorts />
        ) : tab === 2 ? (
          <ClientProcesses />
        ) : (
          <ClientAlerts />
        )}
      </DrawerLayout>
    </>
  )
}

const getBarColor = (percentage: string): "primary" | "warning" | "error" => {
  const value = isNaN(parseInt(percentage)) ? 0 : parseInt(percentage)

  if (value > 90) {
    return "error"
  } else if (value > 70) {
    return "warning"
  } else {
    return "primary"
  }
}

let interval: any = null

function ClientStats({ details }: { details: any }) {
  const [api] = useApi()
  const router = useRouter()

  const [client, setClient] = useState<any>({})
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    if (router.query.id) {
      fetchClient(router.query.id as string)
    }

    const fetchAlertsWrapper = () => {
      if (router.query.id) {
        fetchClient(router.query.id as string)
      }
    }

    interval = setInterval(fetchAlertsWrapper, 60000)

    return () => {
      clearInterval(interval)
    }

    // eslint-disable-next-line
  }, [router.query])

  const fetchClient = async (id: string) => {
    try {
      const response = await api({
        uri: `${ENDPOINTS.clients}/getstats?id=${id}`,
      })

      setClient({
        ...response,
        cpuUsage: response.cpu / 100,
        memoryUsage: response?.memory?.percentage / 100,
      })
    } catch (err) {
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Box
        sx={{
          mb: 1,
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
        }}
      >
        <Heading>Users Online :</Heading>
        <Stack direction="row" spacing={1} sx={{ ml: 1 }}>
          {details?.users
            ? details?.users
                ?.split(",")
                .map((user: any, i: number) => (
                  <Chip key={i} label={user} color="primary" size="small" />
                ))
            : 0}
        </Stack>
      </Box>

      <Typography component="p" variant="caption" sx={{ color: "grey", mb: 1 }}>
        <u>Last Update</u> : {client?.time}
      </Typography>

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
        <Box>
          <Box
            sx={{
              gap: 4,
              display: "flex",
              flexDirection: "row",
              alignItems: "center",
            }}
          >
            <Card variant="outlined" sx={{ height: "100%" }}>
              <CardContent>
                <Box
                  sx={{
                    display: "flex",
                    flexDirection: "row",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <Typography variant="h5" component="div">
                    CPU Usage
                  </Typography>
                  <Box sx={{ width: 200, maxHeight: 150 }}>
                    <Gauge data={client.cpuUsage || 0} />
                  </Box>
                </Box>
              </CardContent>
            </Card>

            <Card variant="outlined" sx={{ height: "100%" }}>
              <CardContent sx={{ height: "100%" }}>
                <Box
                  sx={{
                    display: "flex",
                    flexDirection: "row",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <Box>
                    <Typography variant="h5" component="div">
                      Ram/Memory: {client?.memory?.total}
                    </Typography>
                    <Typography
                      sx={{ mt: 1.5 }}
                      variant="subtitle1"
                      color="text.secondary"
                    >
                      <strong>Available:</strong> {client?.memory?.available}
                    </Typography>
                  </Box>
                  <Box sx={{ width: 200, maxHeight: 150 }}>
                    <Gauge data={client.memoryUsage || 0} />
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>

          <Heading sx={{ my: 1 }}>Disks</Heading>

          <Grid container spacing={4}>
            {client?.disks?.map((disk: any, index: number) => {
              return (
                <Grid item key={index} xs={6} sm={4} lg={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography
                        variant="h5"
                        component="div"
                        sx={{
                          display: "flex",
                          alignItems: "center",
                        }}
                      >
                        <Chip size="small" color="primary" label="Mounted on" />
                        &nbsp;&nbsp;
                        {disk.mounted_on}{" "}
                      </Typography>

                      <Typography
                        sx={{ mt: 1.5 }}
                        variant="subtitle1"
                        color="text.secondary"
                      >
                        <strong>File System:</strong> {disk.filesystem}
                        &nbsp;&nbsp;&nbsp;
                        <strong>Size:</strong> {disk.size}
                      </Typography>
                      <Typography variant="subtitle1" color="text.secondary">
                        <strong>Available:</strong> {disk.avail}{" "}
                        &nbsp;&nbsp;&nbsp;
                        <strong>Used:</strong> {disk.used}
                      </Typography>
                      <Typography variant="subtitle1" color="text.secondary">
                        <strong>Usage:</strong> {disk["use%"]}
                      </Typography>
                      <Box sx={{ width: "100%", mt: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          color={getBarColor(disk["use%"])}
                          value={+disk["use%"].replace("%", "")}
                        />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              )
            })}
          </Grid>
        </Box>
      )}
    </>
  )
}

function ClientPorts() {
  const [api] = useApi()
  const router = useRouter()

  const [data, setData] = useState<any>("")
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    if (router.query.id) {
      fetchClientPorts(router.query.id as string)
    }

    // eslint-disable-next-line
  }, [router.query])

  const fetchClientPorts = async (id: string) => {
    try {
      setLoading(true)

      const response = await api({
        method: "GET",
        uri: `${ENDPOINTS.clients}/getports?id=${id}`,
      })

      setData(response)
    } catch (err) {
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Heading sx={{ mb: 1 }}>Client Ports </Heading>

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
        <Box
          sx={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
          }}
        >
          <Card
            variant="outlined"
            sx={{ height: "100%", borderColor: "green" }}
          >
            <CardContent
              sx={{
                "&:last-child": {
                  pb: 0,
                },
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  flexDirection: "row",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <IconButton
                  onClick={() => fetchClientPorts(router.query.id as string)}
                >
                  <Refresh />
                </IconButton>
                <Typography variant="caption" sx={{ color: "grey" }}>
                  <u>Last Update</u> : {data?.time}
                </Typography>
              </Box>

              <pre>{data?.open_ports}</pre>
            </CardContent>
          </Card>
        </Box>
      )}
    </>
  )
}

function ClientProcesses() {
  const [api] = useApi()
  const router = useRouter()

  const [data, setData] = useState<any>("")
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    if (router.query.id) {
      fetchClientProcesses(router.query.id as string)
    }

    // eslint-disable-next-line
  }, [router.query])

  const fetchClientProcesses = async (id: string) => {
    try {
      setLoading(true)

      const response = await api({
        method: "GET",
        uri: `${ENDPOINTS.clients}/getprocesses?id=${id}`,
      })

      setData(response)
    } catch (err) {
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Heading sx={{ mb: 1 }}>Client Processes</Heading>

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
        <Box
          sx={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
          }}
        >
          <Card
            variant="outlined"
            sx={{ height: "100%", borderColor: "green" }}
          >
            <CardContent
              sx={{
                "&:last-child": {
                  pb: 0,
                },
              }}
            >
              <Box
                sx={{
                  display: "flex",
                  flexDirection: "row",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
              >
                <IconButton
                  onClick={() =>
                    fetchClientProcesses(router.query.id as string)
                  }
                >
                  <Refresh />
                </IconButton>
                <Typography variant="caption" sx={{ color: "grey" }}>
                  <u>Last Update</u> : {data?.time}
                </Typography>
              </Box>
              <pre>{data?.process_list}</pre>{" "}
            </CardContent>
          </Card>
        </Box>
      )}
    </>
  )
}

function ClientAlerts() {
  const [api] = useApi()
  const theme = useTheme()
  const router = useRouter()

  const [tab, setTab] = useState<number>(0)
  const [data, setData] = useState<any>([])
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    if (router.query.id) {
      fetchAlerts(router.query.id as string)
    }

    function checkAndFetchItems() {
      if (router.query.id) {
        fetchAlerts(router.query.id as string)
      }
    }

    interval = setInterval(checkAndFetchItems, 60000)

    return () => {
      clearInterval(interval)
    }

    // eslint-disable-next-line
  }, [router.query, tab])

  const fetchAlerts = async (id: string) => {
    try {
      setLoading(true)

      const response = await api({
        method: "GET",
        uri: `${ENDPOINTS.clients}/getalerts?id=${id}&type=${
          tab === 0 ? "normal" : "custom"
        }`,
      })

      setData(
        response.map((item: any) => ({
          ...item,
          status: item.status === "read" ? "new" : item.status,
        }))
      )
    } catch (err) {
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    {
      id: "time",
      label: "Created At",
      format: (value: any) => new Date(value).toLocaleString(),
    },
    {
      label: "Type",
      id: "alert_type",
    },
    {
      id: "description",
      label: "Description",
    },
    {
      id: "actions",
      label: "Actions",
      render: (row: any) => (
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
          }}
        >
          <Dialog
            fullWidth
            maxWidth="xl"
            title="Alert Details"
            trigger={({ toggleOpen }: { toggleOpen: () => void }) => (
              <IconButton
                size="small"
                sx={{ mr: 1 }}
                aria-label="view"
                onClick={toggleOpen}
                tooltip="View Difference"
              >
                <Visibility fontSize="inherit" />
              </IconButton>
            )}
            content={() => (
              <>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  <strong>Details:</strong> {row.alert_text}
                </Typography>
                <Typography variant="body1" sx={{ mb: 1 }}>
                  <strong>Description:</strong> {row.description}
                </Typography>
                {row.alert_type === "Change in Crontab" && (
                  <>
                    <Typography variant="body1" sx={{ mb: 1 }}>
                      <strong>Difference:</strong>
                    </Typography>
                    <ReactDiffViewer
                      splitView={true}
                      newValue={row.crontab_after}
                      oldValue={row.crontab_before}
                      useDarkTheme={theme.palette.mode === "dark"}
                    />
                  </>
                )}
              </>
            )}
          />

          <EditStatus
            value={row}
            onSubmit={(value: any) => {
              let rows = [...data]
              let index = rows.findIndex((e) => e.id === value.id)
              rows[index] = value
              setData(rows)
            }}
          />
        </Box>
      ),
    },
  ]

  return (
    <>
      <Tabs
        value={tab}
        sx={{ mb: 2, mr: 2 }}
        aria-label="alert-tabs"
        onChange={(_: React.SyntheticEvent, value: number) => setTab(value)}
      >
        <Tab label="Normal" id={`alert-tab-0`} aria-controls={`alert-tab-0`} />
        <Tab label="Custom" id={`alert-tab-1`} aria-controls={`alert-tab-1`} />
      </Tabs>

      <DataTable data={data} columns={columns} loading={loading} />
    </>
  )
}

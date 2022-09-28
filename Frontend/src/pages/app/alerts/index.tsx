import Head from "next/head"
import { useState, useEffect } from "react"
import ReactDiffViewer from "react-diff-viewer"

import { Box } from "@mui/material"
import { Tabs, Tab } from "@mui/material"
import { Typography } from "@mui/material"
import { useTheme } from "@mui/material/styles"
import { Visibility } from "@mui/icons-material"

import { useApi } from "@hooks/useApi"
import { EditStatus } from "@forms/alerts"
import { APP_NAME } from "@utils/constants"
import { Dialog } from "@components/Dialog"
import { ENDPOINTS } from "@utils/constants"
import { DrawerLayout } from "@layouts/Drawer"
import { DataTable } from "@components/DataTable"
import { IconButton } from "@components/IconButton"

let interval: any = null

export default function Alerts() {
  const [api] = useApi()
  const theme = useTheme()

  const [tab, setTab] = useState<number>(0)
  const [data, setData] = useState<any>([])
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    fetchAlerts()

    interval = setInterval(fetchAlerts, 60000)

    return () => {
      clearInterval(interval)
    }

    // eslint-disable-next-line
  }, [tab])

  const fetchAlerts = async () => {
    try {
      setLoading(true)

      const response = await api({
        method: "GET",
        uri: `${ENDPOINTS.clients}/getalerts?type=${
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
      id: "host_name",
      label: "Client Name",
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
      <Head>
        <title>Client Alerts - {APP_NAME}</title>
      </Head>

      <DrawerLayout title="Alerts">
        <Tabs
          value={tab}
          sx={{ mb: 2, mr: 2 }}
          aria-label="alert-tabs"
          onChange={(_: React.SyntheticEvent, value: number) => setTab(value)}
        >
          <Tab
            label="Normal"
            id={`alert-tab-0`}
            aria-controls={`alert-tab-0`}
          />
          <Tab
            label="Custom"
            id={`alert-tab-1`}
            aria-controls={`alert-tab-1`}
          />
        </Tabs>

        <DataTable data={data} columns={columns} loading={loading} />
      </DrawerLayout>
    </>
  )
}

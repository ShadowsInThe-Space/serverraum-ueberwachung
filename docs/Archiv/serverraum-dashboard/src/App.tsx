import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Activity, Droplets, Wind, Siren, Settings, AlertTriangle, CheckCircle, Wifi, Clock, Thermometer, Gauge } from 'lucide-react'

// Mock data for charts
const temperatureData = [
  { time: '00:00', value: 18.5 },
  { time: '04:00', value: 17.2 },
  { time: '08:00', value: 19.8 },
  { time: '12:00', value: 24.5 },
  { time: '16:00', value: 26.3 },
  { time: '20:00', value: 23.1 },
  { time: '24:00', value: 21.0 },
]

const sensors = [
  { id: 1, name: 'Temperatur', value: '22.5°C', icon: Thermometer, status: 'normal', color: 'text-green-500' },
  { id: 2, name: 'Luftfeuchtigkeit', value: '45%', icon: Droplets, status: 'normal', color: 'text-blue-500' },
  { id: 3, name: 'Rauchgas', value: '150 ppm', icon: Wind, status: 'warning', color: 'text-yellow-500' },
  { id: 4, name: 'Bewegung', value: 'Keine', icon: Siren, status: 'normal', color: 'text-green-500' },
]

const alarms = [
  { id: 1, sensor: 'MQ-2', type: 'Rauchgas', value: '150 ppm', threshold: '200 ppm', time: '15:28:00', status: 'active' },
  { id: 2, sensor: 'DHT22', type: 'Temperatur', value: '31.2°C', threshold: '30°C', time: '14:15:00', status: 'acknowledged' },
  { id: 3, sensor: 'PIR', type: 'Bewegung', value: 'true', threshold: '-', time: '10:30:00', status: 'resolved' },
]

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity className="w-6 h-6 text-cyan-400" />
            <h1 className="text-xl font-bold">Serverraum-Überwachung</h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Wifi className="w-4 h-4 text-green-500" />
              <span>ESP32-001</span>
              <span className="text-green-500">●</span>
            </div>
            <Button variant="ghost" size="icon">
              <Settings className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-slate-800 mb-6">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="history">Verlauf</TabsTrigger>
            <TabsTrigger value="alarms">Alarme</TabsTrigger>
            <TabsTrigger value="settings">Einstellungen</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {sensors.map((sensor) => (
                <Card key={sensor.id} className="bg-slate-800 border-slate-700">
                  <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                      <sensor.icon className={`w-6 h-6 ${sensor.color}`} />
                      <Badge variant={sensor.status === 'normal' ? 'default' : 'destructive'}>
                        {sensor.status === 'normal' ? 'Normal' : 'Warnung'}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{sensor.value}</div>
                    <div className="text-sm text-slate-400">{sensor.name}</div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Status Bar */}
            <Card className="bg-slate-800 border-slate-700 mb-6">
              <CardContent className="py-3 flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <Clock className="w-4 h-4" />
                  <span>Letzte Aktualisierung: 15:30:00</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <Wifi className="w-4 h-4" />
                  <span>WLAN: -45 dBm</span>
                </div>
              </CardContent>
            </Card>

            {/* Active Alarm */}
            <Card className="bg-yellow-900/20 border-yellow-700">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-yellow-500">
                  <AlertTriangle className="w-5 h-5" />
                  Aktive Alarme
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between p-3 bg-yellow-900/30 rounded-lg">
                  <div>
                    <div className="font-medium">Rauchgas überschritten (150 ppm)</div>
                    <div className="text-sm text-slate-400">Sensor: MQ-2 | Zeit: 15:28:00</div>
                  </div>
                  <Button variant="outline" size="sm">Quittieren</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle>Verlauf - Temperatur</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={temperatureData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="time" stroke="#94a3b8" />
                      <YAxis stroke="#94a3b8" />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                        labelStyle={{ color: '#f1f5f9' }}
                      />
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#06b6d4"
                        strokeWidth={2}
                        dot={{ fill: '#06b6d4' }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-4 grid grid-cols-3 gap-4 text-center">
                  <div className="p-3 bg-slate-700/50 rounded-lg">
                    <div className="text-2xl font-bold text-cyan-400">22.3°C</div>
                    <div className="text-sm text-slate-400">Durchschnitt</div>
                  </div>
                  <div className="p-3 bg-slate-700/50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-400">18.5°C</div>
                    <div className="text-sm text-slate-400">Min</div>
                  </div>
                  <div className="p-3 bg-slate-700/50 rounded-lg">
                    <div className="text-2xl font-bold text-red-400">28.7°C</div>
                    <div className="text-sm text-slate-400">Max</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Alarms Tab */}
          <TabsContent value="alarms">
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle>Alarme</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow className="border-slate-700">
                      <TableHead className="text-slate-300">Status</TableHead>
                      <TableHead className="text-slate-300">Sensor</TableHead>
                      <TableHead className="text-slate-300">Typ</TableHead>
                      <TableHead className="text-slate-300">Wert</TableHead>
                      <TableHead className="text-slate-300">Zeit</TableHead>
                      <TableHead className="text-slate-300">Aktion</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {alarms.map((alarm) => (
                      <TableRow key={alarm.id} className="border-slate-700">
                        <TableCell>
                          <Badge variant={alarm.status === 'active' ? 'destructive' : alarm.status === 'acknowledged' ? 'outline' : 'secondary'}>
                            {alarm.status === 'active' ? 'Aktiv' : alarm.status === 'acknowledged' ? 'Quittiert' : 'Gelöst'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-slate-300">{alarm.sensor}</TableCell>
                        <TableCell className="text-slate-300">{alarm.type}</TableCell>
                        <TableCell className="text-slate-300">{alarm.value}</TableCell>
                        <TableCell className="text-slate-300">{alarm.time}</TableCell>
                        <TableCell>
                          {alarm.status === 'active' && (
                            <Button variant="outline" size="sm">Quittieren</Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Sidebar */}
              <Card className="bg-slate-800 border-slate-700 lg:col-span-1">
                <CardHeader>
                  <CardTitle>Konfiguration</CardTitle>
                </CardHeader>
                <CardContent>
                  <nav className="space-y-2">
                    <Button variant="ghost" className="w-full justify-start text-left text-slate-300">Sensoren</Button>
                    <Button variant="ghost" className="w-full justify-start text-left text-slate-300">Alarmierung</Button>
                    <Button variant="ghost" className="w-full justify-start text-left text-slate-300">MQTT</Button>
                    <Button variant="ghost" className="w-full justify-start text-left text-slate-300">E-Mail</Button>
                    <Button variant="ghost" className="w-full justify-start text-left text-slate-300">System</Button>
                  </nav>
                </CardContent>
              </Card>

              {/* Settings Form */}
              <Card className="bg-slate-800 border-slate-700 lg:col-span-2">
                <CardHeader>
                  <CardTitle>Sensor: DHT22 (Temperatur & Feuchte)</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-slate-400">Name</label>
                      <input type="text" value="Temperatur & Feuchte" className="w-full mt-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-slate-100" />
                    </div>
                    <div>
                      <label className="text-sm text-slate-400">GPIO-Pin</label>
                      <input type="number" value="5" className="w-full mt-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-slate-100" />
                    </div>
                  </div>
                  <div>
                    <label className="text-sm text-slate-400">Einheit</label>
                    <input type="text" value="°C/%" className="w-full mt-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-slate-100" />
                  </div>
                  <div className="flex items-center gap-2">
                    <input type="checkbox" id="active" defaultChecked className="w-4 h-4" />
                    <label htmlFor="active" className="text-sm text-slate-300">Sensor aktiv</label>
                  </div>
                  <div className="border-t border-slate-700 pt-4">
                    <h4 className="font-medium mb-3">Schwellwerte</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm text-slate-400">Min (°C)</label>
                        <input type="number" value="15.0" className="w-full mt-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-slate-100" />
                      </div>
                      <div>
                        <label className="text-sm text-slate-400">Max (°C)</label>
                        <input type="number" value="30.0" className="w-full mt-1 px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-slate-100" />
                      </div>
                    </div>
                  </div>
                  <div className="border-t border-slate-700 pt-4">
                    <h4 className="font-medium mb-3">Alarmierung</h4>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <input type="checkbox" id="email" defaultChecked className="w-4 h-4" />
                        <label htmlFor="email" className="text-sm text-slate-300">E-Mail</label>
                      </div>
                      <div className="flex items-center gap-2">
                        <input type="checkbox" id="led" defaultChecked className="w-4 h-4" />
                        <label htmlFor="led" className="text-sm text-slate-300">LED</label>
                      </div>
                      <div className="flex items-center gap-2">
                        <input type="checkbox" id="buzzer" className="w-4 h-4" />
                        <label htmlFor="buzzer" className="text-sm text-slate-300">Buzzer</label>
                      </div>
                      <div className="flex items-center gap-2">
                        <input type="checkbox" id="dashboard" defaultChecked className="w-4 h-4" />
                        <label htmlFor="dashboard" className="text-sm text-slate-300">Dashboard</label>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2 pt-4">
                    <Button>Speichern</Button>
                    <Button variant="outline">Abbrechen</Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

export default App

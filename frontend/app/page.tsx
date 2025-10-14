'use client'

import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const API_BASE = 'http://localhost:8000'

export default function Dashboard() {
  const [ticker, setTicker] = useState('AAPL')
  const [tickers, setTickers] = useState<string[]>([])
  const [sentimentData, setSentimentData] = useState<any[]>([])
  const [metrics, setMetrics] = useState<any>({})
  const [latest, setLatest] = useState<any>({})

  useEffect(() => {
    // Remove body margins globally
    document.body.style.margin = '0'
    document.body.style.padding = '0'
    document.body.style.backgroundColor = '#000'
    document.body.style.color = '#fff'
    document.body.style.fontFamily = `'Georgia', 'Times New Roman', serif`

    fetch(`${API_BASE}/tickers`)
      .then(res => res.json())
      .then(data => setTickers(data))
  }, [])

  useEffect(() => {
    const fetchData = () => {
      fetch(`${API_BASE}/sentiment/series?ticker=${ticker}&from_hours=24`)
        .then(res => res.json())
        .then(data => {
          const formatted = data.reverse().map((d: any) => ({
            time: new Date(d.bucket).toLocaleTimeString(),
            sentiment: d.vw_sentiment,
            posts: d.n_posts
          }))
          setSentimentData(formatted)
        })

      fetch(`${API_BASE}/sentiment/latest?ticker=${ticker}`)
        .then(res => res.json())
        .then(data => setLatest(data))

      fetch(`${API_BASE}/metrics/pipeline`)
        .then(res => res.json())
        .then(data => setMetrics(data))
    }

    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [ticker])

  return (
    <div
      style={{
        fontFamily: `'Georgia', 'Times New Roman', serif`,
        backgroundColor: '#000',
        color: '#fff',
        minHeight: '100vh',
        margin: 0,
        padding: '20px',
        boxSizing: 'border-box'
      }}
    >
      <h1 style={{ fontWeight: 'normal' }}>BullBear Debates Dashboard</h1>

      <div style={{ marginBottom: '20px' }}>
        <label style={{ fontWeight: 'normal' }}>Select Ticker: </label>
        <select
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          style={{
            padding: '8px',
            fontSize: '16px',
            fontFamily: `'Georgia', 'Times New Roman', serif`,
            backgroundColor: '#111',
            color: '#fff',
            border: '1px solid #555',
            borderRadius: '5px'
          }}
        >
          {tickers.map(t => (
            <option key={t} value={t} style={{ color: '#000' }}>
              {t}
            </option>
          ))}
        </select>
      </div>

      <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
        {[
          { label: 'P95 Latency', value: `${metrics.p95_latency_sec || 0}s` },
          { label: 'Posts (5min)', value: metrics.last_5m_count || 0 },
          { label: 'Positive', value: latest.pos_ct || 0 },
          { label: 'Neutral', value: latest.neu_ct || 0 },
          { label: 'Negative', value: latest.neg_ct || 0 }
        ].map((item, idx) => (
          <div
            key={idx}
            style={{
              padding: '15px',
              border: '1px solid #444',
              borderRadius: '8px',
              backgroundColor: '#111',
              fontWeight: 'normal'
            }}
          >
            {item.label}: {item.value}
          </div>
        ))}
      </div>

      <h2 style={{ fontWeight: 'normal' }}>Volume-Weighted Sentiment (Last 6 Hours)</h2>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={sentimentData}>
          <CartesianGrid stroke="#333" strokeDasharray="3 3" />
          <XAxis dataKey="time" stroke="#fff" />
          <YAxis domain={[-1, 1]} stroke="#fff" />
          <Tooltip
            contentStyle={{
              backgroundColor: '#111',
              border: '1px solid #555',
              color: '#fff',
              fontFamily: `'Georgia', 'Times New Roman', serif`
            }}
          />
          <Legend wrapperStyle={{ color: '#fff', fontWeight: 'normal' }} />
          <Line type="monotone" dataKey="sentiment" stroke="#00bfff" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

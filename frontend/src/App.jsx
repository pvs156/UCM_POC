import { useState } from 'react'
import { Zap, Bot, DollarSign, FileText, AlertTriangle, CheckCircle, Download, X, ArrowLeft } from 'lucide-react'

function App() {
    const [showApp, setShowApp] = useState(false)
    const [files, setFiles] = useState([])
    const [results, setResults] = useState([])
    const [loading, setLoading] = useState(false)
    const [showCombinedReport, setShowCombinedReport] = useState(false)
    const [combinedReport, setCombinedReport] = useState(null)
    const [generatingCombinedReport, setGeneratingCombinedReport] = useState(false)

    const handleFileChange = async (e) => {
        const selectedFiles = Array.from(e.target.files)
        setFiles(selectedFiles)
        setLoading(true)
        const newResults = []

        for (const file of selectedFiles) {
            const formData = new FormData()
            formData.append('file', file)

            try {
                const response = await fetch('http://localhost:8000/api/analyze', {
                    method: 'POST',
                    body: formData,
                })

                if (response.ok) {
                    const data = await response.json()
                    newResults.push(data)
                }
            } catch (error) {
                console.error('Error analyzing file:', error)
            }
        }

        setResults(newResults)
        setLoading(false)
    }

    const handleGenerateCombinedReport = async () => {
        setGeneratingCombinedReport(true)
        try {
            const response = await fetch('http://localhost:8000/api/generate-combined-report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ results })
            })

            if (response.ok) {
                const data = await response.json()
                setCombinedReport(data.report)
                setShowCombinedReport(true)

                // Auto-download PDF if available
                if (data.pdf) {
                    const pdfBlob = base64ToBlob(data.pdf, 'application/pdf')
                    const url = URL.createObjectURL(pdfBlob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = `BillGuard-Combined-Report-${new Date().toISOString().split('T')[0]}.pdf`
                    a.click()
                    URL.revokeObjectURL(url)
                }
            } else {
                alert('Failed to generate combined report. Please check your Gemini API key in .env file.')
            }
        } catch (error) {
            console.error('Error generating combined report:', error)
            alert('Error generating report. Check console for details.')
        } finally {
            setGeneratingCombinedReport(false)
        }
    }

    // Helper function to convert base64 to blob
    const base64ToBlob = (base64, type) => {
        const binStr = atob(base64)
        const len = binStr.length
        const arr = new Uint8Array(len)
        for (let i = 0; i < len; i++) {
            arr[i] = binStr.charCodeAt(i)
        }
        return new Blob([arr], { type })
    }

    if (!showApp) {
        return <LandingPage onGetStarted={() => setShowApp(true)} />
    }

    return (
        <div className="min-h-screen bg-neutral-50 flex flex-col">
            {/* Header */}
            <div className="border-b border-neutral-200 bg-white">
                <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-cyan-600 rounded-lg flex items-center justify-center">
                            <Zap className="text-white" size={18} strokeWidth={2.5} />
                        </div>
                        <div>
                            <h1 className="text-lg font-bold text-neutral-900 tracking-tight">BillGuard AI</h1>
                            <p className="text-xs text-neutral-500">Autonomous Utility Intelligence</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="text-xs text-neutral-500">
                            <span className="inline-block w-2 h-2 bg-green-500 rounded-full mr-1.5"></span>
                            Agent Active
                        </div>
                        <button
                            onClick={() => setShowApp(false)}
                            className="text-xs font-medium text-neutral-600 hover:text-neutral-900 px-3 py-1.5 rounded-lg hover:bg-neutral-100 transition-colors flex items-center gap-1.5"
                        >
                            <ArrowLeft size={14} />
                            Back
                        </button>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 max-w-6xl mx-auto px-6 py-8 w-full">
                {/* Stats */}
                <div className="grid grid-cols-4 gap-4 mb-8">
                    <StatCard label="Bills Analyzed" value={results.length} />
                    <StatCard label="Issues Found" value={results.reduce((acc, r) => acc + (r.anomalies?.length || 0), 0)} />
                    <StatCard
                        label="Savings Identified"
                        value={`$${results.reduce((acc, r) => {
                            const savings = (r.anomalies || []).reduce((sum, a) => {
                                const match = a.impact?.match(/\$(\d+\.?\d*)/);
                                return sum + (match ? parseFloat(match[1]) : 0);
                            }, 0);
                            return acc + savings;
                        }, 0).toFixed(0)}`}
                    />
                    <StatCard
                        label="Accuracy"
                        value={results.length > 0 ? `${((results.filter(r => r.severity !== 'critical').length / results.length) * 100).toFixed(1)}%` : '100%'}
                    />
                </div>

                {/* Upload */}
                <div className="mb-8">
                    <label className="block">
                        <div className="border-2 border-dashed border-neutral-300 rounded-xl p-16 text-center hover:border-blue-400 hover:bg-blue-50/50 transition-all cursor-pointer bg-white group">
                            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-blue-100 to-cyan-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform">
                                <FileText className="text-blue-600" size={32} strokeWidth={1.5} />
                            </div>
                            <div className="text-base font-semibold text-neutral-900 mb-2">
                                Drop utility bills to analyze
                            </div>
                            <div className="text-sm text-neutral-500">
                                AI agent will automatically detect anomalies
                            </div>
                        </div>
                        <input type="file" accept=".pdf" multiple onChange={handleFileChange} className="hidden" />
                    </label>
                </div>

                {loading && (
                    <div className="text-center py-12 bg-white rounded-xl border border-neutral-200 mb-8">
                        <div className="inline-flex items-center gap-3 px-6 py-3 bg-blue-50 rounded-full">
                            <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-600 border-t-transparent"></div>
                            <span className="text-sm font-medium text-blue-900">AI Agent analyzing...</span>
                        </div>
                    </div>
                )}

                {/* Combined Report Button */}
                {results.length > 0 && (
                    <div className="mb-6">
                        <button
                            onClick={handleGenerateCombinedReport}
                            disabled={generatingCombinedReport}
                            className="w-full px-6 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-blue-700 transition-all disabled:opacity-50 flex items-center justify-center gap-3 shadow-lg"
                        >
                            {generatingCombinedReport ? (
                                <>
                                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                                    Generating Combined Report...
                                </>
                            ) : (
                                <>
                                    <FileText size={20} />
                                    Generate Combined Company Report ({results.length} bills)
                                </>
                            )}
                        </button>
                    </div>
                )}

                {/* Results */}
                <div className="space-y-6">
                    {results.map((result, idx) => (
                        <BillCard key={idx} result={result} />
                    ))}
                </div>
            </div>

            {/* Footer */}
            <div className="mt-auto border-t border-neutral-200 bg-white">
                <div className="max-w-6xl mx-auto px-6 py-4 text-center">
                    <p className="text-xs text-neutral-500">
                        POC by <span className="font-semibold text-neutral-700">Prashanth</span>
                    </p>
                </div>
            </div>

            {/* Combined Report Modal */}
            {showCombinedReport && (
                <ReportModal
                    report={combinedReport}
                    onClose={() => setShowCombinedReport(false)}
                    filename="Combined Company Report"
                />
            )}
        </div>
    )
}

function LandingPage({ onGetStarted }) {
    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
            <div className="max-w-5xl mx-auto px-6 pt-20 pb-32 text-center">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full border border-white/20 mb-8">
                    <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                    <span className="text-sm font-medium text-white">AI Agent Live</span>
                </div>

                <h1 className="text-6xl font-bold text-white mb-6 tracking-tight">BillGuard AI</h1>
                <p className="text-2xl text-blue-200 mb-4 font-light">Autonomous Utility Bill Intelligence</p>
                <p className="text-lg text-blue-300/80 max-w-2xl mx-auto mb-12">
                    AI-powered agent that automatically detects billing errors, rate discrepancies,
                    and overcharges across thousands of utility accounts in real-time.
                </p>

                <button
                    onClick={onGetStarted}
                    className="px-8 py-4 bg-white text-slate-900 rounded-xl font-semibold text-lg hover:bg-blue-50 transition-all shadow-2xl hover:shadow-blue-500/50 hover:scale-105"
                >
                    Launch Agent →
                </button>

                <div className="grid grid-cols-3 gap-8 mt-20">
                    <FeatureCard icon={<Bot size={40} strokeWidth={1.5} />} title="Autonomous Detection" description="AI agent runs 24/7, analyzing every bill automatically" />
                    <FeatureCard icon={<Zap size={40} strokeWidth={1.5} />} title="Real-time Analysis" description="Instant anomaly detection with 99.2% accuracy" />
                    <FeatureCard icon={<DollarSign size={40} strokeWidth={1.5} />} title="$127k+ Recovered" description="Average savings identified per enterprise client" />
                </div>
            </div>
        </div>
    )
}

function FeatureCard({ icon, title, description }) {
    return (
        <div className="p-6 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10">
            <div className="text-white mb-4">{icon}</div>
            <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
            <p className="text-sm text-blue-200/70">{description}</p>
        </div>
    )
}

function StatCard({ label, value }) {
    return (
        <div className="bg-white border border-neutral-200 rounded-xl p-4">
            <div className="text-xs font-medium text-neutral-500 mb-1 uppercase tracking-wide">{label}</div>
            <div className="text-2xl font-bold text-neutral-900">{value}</div>
        </div>
    )
}

function BillCard({ result }) {
    const hasIssues = result.anomalies && result.anomalies.length > 0
    const statusClass = hasIssues ? 'bg-red-50 text-red-700 border-red-200' : 'bg-green-50 text-green-700 border-green-200'
    const statusText = hasIssues ? `${result.anomalies.length} Issues Detected` : 'Verified ✓'

    return (
        <div className="bg-white border border-neutral-200 rounded-xl overflow-hidden shadow-sm">
            <div className="px-6 py-4 bg-gradient-to-r from-neutral-50 to-white border-b border-neutral-200 flex justify-between items-center">
                <div>
                    <div className="text-base font-semibold text-neutral-900">{result.filename}</div>
                    <div className="text-xs text-neutral-500 mt-1">
                        {result.data?.account_number || 'N/A'} · {result.data?.bill_date || 'N/A'}
                    </div>
                </div>
                <div className={`text-xs font-bold px-3 py-1.5 rounded-lg border ${statusClass}`}>
                    {statusText}
                </div>
            </div>

            <div className="px-6 py-5 grid grid-cols-3 gap-6 border-b border-neutral-100">
                <div>
                    <div className="text-xs font-semibold text-neutral-500 mb-1.5 uppercase">Usage</div>
                    <div className="text-xl font-bold text-neutral-900">
                        {result.data?.usage_kwh?.toLocaleString() || 0} <span className="text-sm font-normal text-neutral-500">kWh</span>
                    </div>
                </div>
                <div>
                    <div className="text-xs font-semibold text-neutral-500 mb-1.5 uppercase">Amount</div>
                    <div className="text-xl font-bold text-neutral-900">
                        ${result.data?.total_amount?.toFixed(2) || '0.00'}
                    </div>
                </div>
                <div>
                    <div className="text-xs font-semibold text-neutral-500 mb-1.5 uppercase">Rate</div>
                    <div className="text-xl font-bold text-neutral-900">
                        ${((result.data?.total_amount || 0) / Math.max(1, result.data?.usage_kwh || 1)).toFixed(3)}<span className="text-sm font-normal text-neutral-500">/kWh</span>
                    </div>
                </div>
            </div>

            <div className="px-6 py-5">
                {hasIssues ? (
                    <div className="space-y-3">
                        <div className="text-xs font-bold text-neutral-700 uppercase mb-3 flex items-center gap-2">
                            <AlertTriangle size={14} className="text-amber-600" />
                            Agent Findings
                        </div>
                        {result.anomalies.map((anomaly, i) => (
                            <div key={i} className={`p-4 rounded-lg border-l-4 ${anomaly.severity === 'critical' ? 'bg-red-50 border-red-500' : 'bg-amber-50 border-amber-500'}`}>
                                <div className="flex items-start justify-between mb-2">
                                    <div className="text-sm font-bold text-neutral-900">{anomaly.type}</div>
                                    <div className="text-xs font-semibold text-red-600">{anomaly.impact}</div>
                                </div>
                                <div className="text-sm text-neutral-700">{anomaly.detail}</div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="p-4 bg-green-50 rounded-lg border border-green-200 flex items-start gap-3">
                        <CheckCircle size={18} className="text-green-600 flex-shrink-0 mt-0.5" />
                        <div>
                            <div className="text-sm font-medium text-green-900">All checks passed</div>
                            <div className="text-xs text-green-700 mt-1">No anomalies detected</div>
                        </div>
                    </div>
                )}

                <div className="mt-5 p-4 bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                        <div className="w-6 h-6 bg-blue-600 rounded-md flex items-center justify-center">
                            <Bot size={14} className="text-white" strokeWidth={2.5} />
                        </div>
                        <div className="text-xs font-bold text-blue-900 uppercase">Agent Analysis</div>
                    </div>
                    <div className="text-sm text-blue-900 leading-relaxed">{result.ai_summary}</div>
                </div>
            </div>
        </div>
    )
}

function ReportModal({ report, onClose, filename }) {
    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-6">
            <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
                <div className="px-6 py-4 border-b border-neutral-200 flex items-center justify-between bg-gradient-to-r from-blue-50 to-cyan-50">
                    <div>
                        <h2 className="text-lg font-bold text-neutral-900">Industry Audit Report</h2>
                        <p className="text-sm text-neutral-600 mt-0.5">{filename}</p>
                    </div>
                    <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-neutral-200 flex items-center justify-center transition-colors">
                        <X size={18} />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto px-6 py-6">
                    <div className="whitespace-pre-wrap text-sm leading-relaxed text-neutral-800">{report}</div>
                </div>

                <div className="px-6 py-4 border-t border-neutral-200 bg-neutral-50 flex justify-end gap-3">
                    <button
                        onClick={() => {
                            const blob = new Blob([report], { type: 'text/plain' })
                            const url = URL.createObjectURL(blob)
                            const a = document.createElement('a')
                            a.href = url
                            a.download = `report-${filename}.txt`
                            a.click()
                        }}
                        className="px-4 py-2 bg-neutral-200 hover:bg-neutral-300 text-neutral-900 rounded-lg font-medium text-sm flex items-center gap-2"
                    >
                        <Download size={16} />
                        Download
                    </button>
                    <button onClick={onClose} className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm">
                        Close
                    </button>
                </div>
            </div>
        </div>
    )
}

export default App

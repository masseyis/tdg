"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/hooks/use-toast"

export default function SpecMintApp() {
  const [isLoading, setIsLoading] = useState(false)
  const [hasResults, setHasResults] = useState(false)
  const [showError, setShowError] = useState(false)
  const [progress, setProgress] = useState(0)
  const [dragActive, setDragActive] = useState(false)
  const [casesPerEndpoint, setCasesPerEndpoint] = useState(12)
  const [selectedOutputs, setSelectedOutputs] = useState<string[]>(["junit", "postman"])
  const [domainHint, setDomainHint] = useState("general")
  const [seed, setSeed] = useState("")
  const [specUrl, setSpecUrl] = useState("")
  const { toast } = useToast()

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const files = e.dataTransfer.files
    if (files && files[0]) {
      const file = files[0]
      const validTypes = ["application/json", "application/x-yaml", "text/yaml", "text/plain"]
      const validExtensions = [".json", ".yaml", ".yml"]

      if (validTypes.includes(file.type) || validExtensions.some((ext) => file.name.toLowerCase().endsWith(ext))) {
        console.log("[v0] Valid file dropped:", file.name)
        // Handle file upload logic here
      }
    }
  }

  const handleGenerate = async () => {
    setIsLoading(true)
    setShowError(false)
    setProgress(0)

    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval)
          return 90
        }
        return prev + 10
      })
    }, 200)

    // Simulate API call
    setTimeout(() => {
      clearInterval(progressInterval)
      setProgress(100)
      setIsLoading(false)
      setHasResults(true)
      toast({
        title: "Artifacts minted ✓",
        description: "Your test cases have been generated successfully.",
      })
    }, 3000)
  }

  const handleRetry = () => {
    setShowError(false)
    handleGenerate()
  }

  const outputOptions = [
    { id: "junit", label: "JUnit" },
    { id: "postman", label: "Postman" },
    { id: "wiremock", label: "WireMock" },
    { id: "json", label: "JSON" },
    { id: "csv", label: "CSV" },
    { id: "sql", label: "SQL" },
  ]

  const mockResults = [
    { endpoint: "/users", method: "POST", cases: 15, artifacts: "JUnit, Postman" },
    { endpoint: "/users/{id}", method: "GET", cases: 12, artifacts: "JUnit, JSON" },
    { endpoint: "/orders", method: "POST", cases: 18, artifacts: "JUnit, Postman, CSV" },
    { endpoint: "/orders/{id}", method: "DELETE", cases: 8, artifacts: "JUnit" },
  ]

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Navigation */}
      <nav className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold font-sans text-teal-400">SpecMint</h1>
            </div>
            <div className="hidden md:flex items-center space-x-8">
              <a href="#dashboard" className="text-gray-300 hover:text-white transition-colors">
                Dashboard
              </a>
              <a href="#docs" className="text-gray-300 hover:text-white transition-colors">
                Docs
              </a>
              <a href="#github" className="text-gray-300 hover:text-white transition-colors">
                GitHub
              </a>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Banner */}
        {showError && (
          <Alert className="mb-6 border-red-600 bg-red-950/50">
            <AlertDescription className="flex items-center justify-between">
              <span>Failed to generate test cases. Please check your specification and try again.</span>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRetry}
                className="border-red-600 text-red-400 hover:bg-red-950 bg-transparent"
              >
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        )}

        <div className="grid lg:grid-cols-4 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-3 space-y-8">
            {/* Input Card */}
            <Card
              className={`bg-gray-900 border-gray-800 rounded-2xl transition-all duration-200 ${
                isLoading ? "animate-pulse" : ""
              }`}
            >
              <CardHeader>
                <CardTitle className="text-teal-400 font-sans">Upload your OpenAPI</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Drag and Drop Zone */}
                <div
                  className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
                    dragActive ? "border-teal-400 bg-teal-950/20" : "border-gray-600 hover:border-gray-500"
                  }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  <div className="space-y-2">
                    <div className="text-4xl">📄</div>
                    <p className="text-gray-300">
                      Drop your OpenAPI spec here or{" "}
                      <button className="text-teal-400 hover:text-teal-300 underline">browse files</button>
                    </p>
                    <p className="text-sm text-gray-500">Supports .yaml, .yml, .json files</p>
                  </div>
                </div>

                {/* URL Input */}
                <div className="space-y-2">
                  <Label htmlFor="spec-url" className="text-gray-300">
                    Or paste a URL
                  </Label>
                  <Input
                    id="spec-url"
                    placeholder="https://api.example.com/openapi.json"
                    value={specUrl}
                    onChange={(e) => setSpecUrl(e.target.value)}
                    className="bg-gray-800 border-gray-700 text-white placeholder-gray-500"
                  />
                </div>

                {/* Options Grid */}
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Cases per endpoint */}
                  <div className="space-y-2">
                    <Label htmlFor="cases" className="text-gray-300">
                      Cases per endpoint
                    </Label>
                    <Input
                      id="cases"
                      type="number"
                      value={casesPerEndpoint}
                      onChange={(e) => setCasesPerEndpoint(Number(e.target.value))}
                      min="1"
                      max="100"
                      className="bg-gray-800 border-gray-700 text-white"
                    />
                  </div>

                  {/* Domain hint */}
                  <div className="space-y-2">
                    <Label className="text-gray-300">Domain hint</Label>
                    <Select value={domainHint} onValueChange={setDomainHint}>
                      <SelectTrigger className="bg-gray-800 border-gray-700 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-gray-800 border-gray-700">
                        <SelectItem value="general">General</SelectItem>
                        <SelectItem value="ecommerce">E-commerce</SelectItem>
                        <SelectItem value="finance">Finance</SelectItem>
                        <SelectItem value="healthcare">Healthcare</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Output formats */}
                <div className="space-y-3">
                  <Label className="text-gray-300">Output formats</Label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {outputOptions.map((option) => (
                      <div key={option.id} className="flex items-center space-x-2">
                        <Checkbox
                          id={option.id}
                          checked={selectedOutputs.includes(option.id)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setSelectedOutputs([...selectedOutputs, option.id])
                            } else {
                              setSelectedOutputs(selectedOutputs.filter((id) => id !== option.id))
                            }
                          }}
                          className="border-gray-600 data-[state=checked]:bg-teal-600"
                        />
                        <Label htmlFor={option.id} className="text-sm text-gray-300">
                          {option.label}
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Seed input */}
                <div className="space-y-2">
                  <Label htmlFor="seed" className="text-gray-300">
                    Seed (optional)
                  </Label>
                  <Input
                    id="seed"
                    placeholder="Enter seed for reproducible results"
                    value={seed}
                    onChange={(e) => setSeed(e.target.value)}
                    className="bg-gray-800 border-gray-700 text-white placeholder-gray-500"
                  />
                </div>

                {/* Generate button */}
                <Button
                  onClick={handleGenerate}
                  disabled={isLoading}
                  className="w-full bg-teal-600 hover:bg-teal-700 text-white py-3"
                >
                  {isLoading ? "Generating..." : "Generate"}
                </Button>
              </CardContent>
            </Card>

            {/* Results Card */}
            <Card
              className={`bg-gray-900 border-gray-800 rounded-2xl transition-all duration-200 ${
                isLoading ? "animate-pulse" : ""
              }`}
            >
              <CardHeader>
                <CardTitle className="text-teal-400 font-sans">Results</CardTitle>
              </CardHeader>
              <CardContent>
                {!hasResults && !isLoading && (
                  <div className="text-center py-12">
                    <div className="text-6xl mb-4">🎯</div>
                    <p className="text-gray-400">No generation yet.</p>
                    <p className="text-sm text-gray-500 mt-2">Upload your OpenAPI spec to get started</p>
                  </div>
                )}

                {isLoading && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-300">Generating test cases...</span>
                      <span className="text-sm text-gray-400">{progress}%</span>
                    </div>
                    <Progress value={progress} className="bg-gray-800" />
                  </div>
                )}

                {hasResults && !isLoading && (
                  <div className="space-y-6">
                    {/* Results table */}
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-gray-700">
                            <th className="text-left py-3 px-2 text-gray-300 font-medium">Endpoint</th>
                            <th className="text-left py-3 px-2 text-gray-300 font-medium">Method</th>
                            <th className="text-left py-3 px-2 text-gray-300 font-medium">Cases</th>
                            <th className="text-left py-3 px-2 text-gray-300 font-medium">Artifacts</th>
                          </tr>
                        </thead>
                        <tbody>
                          {mockResults.map((result, index) => (
                            <tr key={index} className="border-b border-gray-800">
                              <td className="py-3 px-2 font-mono text-sm">{result.endpoint}</td>
                              <td className="py-3 px-2">
                                <Badge
                                  variant="outline"
                                  className={`${
                                    result.method === "POST"
                                      ? "border-green-600 text-green-400"
                                      : result.method === "GET"
                                        ? "border-blue-600 text-blue-400"
                                        : "border-red-600 text-red-400"
                                  }`}
                                >
                                  {result.method}
                                </Badge>
                              </td>
                              <td className="py-3 px-2 text-gray-300">{result.cases}</td>
                              <td className="py-3 px-2 text-sm text-gray-400">{result.artifacts}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Action buttons */}
                    <div className="flex flex-col sm:flex-row gap-3">
                      <Button className="bg-teal-600 hover:bg-teal-700 text-white">Download ZIP</Button>
                      <Button
                        variant="outline"
                        className="border-gray-600 text-gray-300 hover:bg-gray-800 bg-transparent"
                      >
                        View summary.json
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Sidebar - Tips */}
          <div className="hidden lg:block">
            <Card className="bg-gray-900 border-gray-800 rounded-2xl sticky top-24">
              <CardHeader>
                <CardTitle className="text-teal-400 font-sans">Tips</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-4 text-sm">
                  <li className="flex items-start gap-3">
                    <span className="text-teal-400 mt-0.5">•</span>
                    <span className="text-gray-300">Use examples in your spec for more realistic test data</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-teal-400 mt-0.5">•</span>
                    <span className="text-gray-300">Include enums to generate boundary test cases</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-teal-400 mt-0.5">•</span>
                    <span className="text-gray-300">Add auth hints in security schemes for better coverage</span>
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

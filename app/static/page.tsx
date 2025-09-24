"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function SpecMintLanding() {
  const [activeTab, setActiveTab] = useState("openapi")

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Navigation */}
      <nav className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold font-[family-name:var(--font-heading)] text-teal-400">SpecMint</h1>
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-8">
                <a href="#product" className="text-gray-300 hover:text-white transition-colors">
                  Product
                </a>
                <a href="#docs" className="text-gray-300 hover:text-white transition-colors">
                  Docs
                </a>
                <a href="#pricing" className="text-gray-300 hover:text-white transition-colors">
                  Pricing
                </a>
                <a href="#github" className="text-gray-300 hover:text-white transition-colors">
                  GitHub
                </a>
              </div>
            </div>
            <Button className="bg-teal-600 hover:bg-teal-700 text-white">Generate test data</Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-20 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-5xl md:text-6xl font-bold font-[family-name:var(--font-heading)] mb-6">
            Mint test cases from your <span className="text-teal-400">API spec</span>
          </h1>
          <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto leading-relaxed">
            Upload your OpenAPI specification and get valid, boundary, and negative test cases plus runnable artifacts.
            Generate JUnit tests, Postman collections, and realistic datasets in seconds.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Button size="lg" className="bg-teal-600 hover:bg-teal-700 text-white px-8 py-3">
              Generate test data
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="border-gray-600 text-gray-300 hover:bg-gray-800 bg-transparent"
            >
              View docs
            </Button>
          </div>

          {/* Trust Bar */}
          <div className="flex items-center justify-center gap-8 text-sm text-gray-400">
            <div className="flex items-center gap-2">
              <span>⭐</span>
              <span>2.1k GitHub stars</span>
            </div>
            <div className="flex items-center gap-2">
              <span>✓</span>
              <span>Works with OpenAPI 3.0/3.1</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="product" className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold font-[family-name:var(--font-heading)] text-center mb-12">
            Everything you need for API testing
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card className="bg-gray-900 border-gray-800 rounded-2xl hover:bg-gray-800/50 transition-colors">
              <CardHeader>
                <CardTitle className="text-teal-400 font-[family-name:var(--font-heading)]">
                  Contract-true test cases
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-300">
                  Generate valid, edge case, and negative test scenarios that perfectly match your API contract.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gray-900 border-gray-800 rounded-2xl hover:bg-gray-800/50 transition-colors">
              <CardHeader>
                <CardTitle className="text-teal-400 font-[family-name:var(--font-heading)]">
                  Multiple artifacts
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-300">
                  Export as JUnit/REST Assured, Python, Node.js, Postman collections, and WireMock stubs.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gray-900 border-gray-800 rounded-2xl hover:bg-gray-800/50 transition-colors">
              <CardHeader>
                <CardTitle className="text-teal-400 font-[family-name:var(--font-heading)]">Stateful flows</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-300">
                  Capture IDs and data across test steps to create realistic end-to-end scenarios.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gray-900 border-gray-800 rounded-2xl hover:bg-gray-800/50 transition-colors">
              <CardHeader>
                <CardTitle className="text-teal-400 font-[family-name:var(--font-heading)]">
                  Schema validation
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-300">
                  Automatic validation against your OpenAPI schema ensures test data integrity.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gray-900 border-gray-800 rounded-2xl hover:bg-gray-800/50 transition-colors">
              <CardHeader>
                <CardTitle className="text-teal-400 font-[family-name:var(--font-heading)]">
                  Realistic datasets
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-300">
                  Generate CSV and SQL datasets with realistic data that matches your API requirements.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-gray-900 border-gray-800 rounded-2xl hover:bg-gray-800/50 transition-colors">
              <CardHeader>
                <CardTitle className="text-teal-400 font-[family-name:var(--font-heading)]">CI/CD ready</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-300">
                  Generated tests integrate seamlessly with your existing CI/CD pipeline and testing framework.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-900/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold font-[family-name:var(--font-heading)] text-center mb-12">How it works</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-teal-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold">1</span>
              </div>
              <h3 className="text-xl font-semibold font-[family-name:var(--font-heading)] mb-2">Upload your spec</h3>
              <p className="text-gray-300">Drop your OpenAPI 3.0 or 3.1 specification file into SpecMint</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-teal-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold">2</span>
              </div>
              <h3 className="text-xl font-semibold font-[family-name:var(--font-heading)] mb-2">Generate tests</h3>
              <p className="text-gray-300">
                Our AI analyzes your spec and creates comprehensive test cases automatically
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-teal-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold">3</span>
              </div>
              <h3 className="text-xl font-semibold font-[family-name:var(--font-heading)] mb-2">Download zip</h3>
              <p className="text-gray-300">Get a complete package with tests, data, and artifacts ready to run</p>
            </div>
          </div>
        </div>
      </section>

      {/* Code Examples */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold font-[family-name:var(--font-heading)] text-center mb-12">
            From spec to tests in seconds
          </h2>
          <div className="max-w-4xl mx-auto">
            <div className="flex border-b border-gray-800 mb-6">
              <button
                onClick={() => setActiveTab("openapi")}
                className={`px-4 py-2 font-medium ${
                  activeTab === "openapi"
                    ? "text-teal-400 border-b-2 border-teal-400"
                    : "text-gray-400 hover:text-white"
                }`}
              >
                OpenAPI Spec
              </button>
              <button
                onClick={() => setActiveTab("junit")}
                className={`px-4 py-2 font-medium ${
                  activeTab === "junit" ? "text-teal-400 border-b-2 border-teal-400" : "text-gray-400 hover:text-white"
                }`}
              >
                Generated JUnit Test
              </button>
            </div>

            <Card className="bg-gray-900 border-gray-800 rounded-2xl">
              <CardContent className="p-6">
                {activeTab === "openapi" ? (
                  <div className="relative">
                    <pre className="text-sm text-gray-300 overflow-x-auto">
                      <code>{`paths:
  /users:
    post:
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                email:
                  type: string
                  format: email
                age:
                  type: integer
                  minimum: 18
                  maximum: 120`}</code>
                    </pre>
                    <Button
                      size="sm"
                      variant="outline"
                      className="absolute top-2 right-2 border-gray-600 text-gray-300 hover:bg-gray-800 bg-transparent"
                    >
                      Copy
                    </Button>
                  </div>
                ) : (
                  <div className="relative">
                    <pre className="text-sm text-gray-300 overflow-x-auto">
                      <code>{`@ParameterizedTest
@ValueSource(strings = {
  "valid@email.com,25",
  "edge@test.com,18",
  "boundary@test.com,120"
})
void testCreateUser(String testData) {
  String[] parts = testData.split(",");
  
  given()
    .contentType("application/json")
    .body(createUserPayload(parts[0], parts[1]))
  .when()
    .post("/users")
  .then()
    .statusCode(201)
    .body("email", equalTo(parts[0]));
}`}</code>
                    </pre>
                    <Button
                      size="sm"
                      variant="outline"
                      className="absolute top-2 right-2 border-gray-600 text-gray-300 hover:bg-gray-800 bg-transparent"
                    >
                      Copy
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-900/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold font-[family-name:var(--font-heading)] text-center mb-12">
            Simple, transparent pricing
          </h2>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <Card className="bg-gray-900 border-gray-800 rounded-2xl">
              <CardHeader>
                <CardTitle className="font-[family-name:var(--font-heading)]">Free</CardTitle>
                <CardDescription className="text-2xl font-bold text-white">
                  $0<span className="text-sm font-normal text-gray-400">/month</span>
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3 mb-6">
                  <li className="flex items-center gap-2">
                    <span className="text-teal-400">✓</span>
                    <span>Unlimited generations</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-teal-400">✓</span>
                    <span>Basic artifacts</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-teal-400">✓</span>
                    <span>Community support</span>
                  </li>
                </ul>
                <Button className="w-full bg-gray-800 hover:bg-gray-700 text-white">Get started</Button>
              </CardContent>
            </Card>

            <Card className="bg-gray-900 border-teal-600 rounded-2xl relative">
              <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-teal-600 text-white">
                Popular
              </Badge>
              <CardHeader>
                <CardTitle className="font-[family-name:var(--font-heading)]">Pro</CardTitle>
                <CardDescription className="text-2xl font-bold text-white">
                  $29<span className="text-sm font-normal text-gray-400">/month</span>
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3 mb-6">
                  <li className="flex items-center gap-2">
                    <span className="text-teal-400">✓</span>
                    <span>Unlimited test cases</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-teal-400">✓</span>
                    <span>All artifact types</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-teal-400">✓</span>
                    <span>Stateful flows</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-teal-400">✓</span>
                    <span>Priority support</span>
                  </li>
                </ul>
                <Button className="w-full bg-teal-600 hover:bg-teal-700 text-white">Get started</Button>
              </CardContent>
            </Card>

            <Card className="bg-gray-900 border-gray-800 rounded-2xl">
              <CardHeader>
                <CardTitle className="font-[family-name:var(--font-heading)]">Team</CardTitle>
                <CardDescription className="text-2xl font-bold text-white">
                  $99<span className="text-sm font-normal text-gray-400">/month</span>
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3 mb-6">
                  <li className="flex items-center gap-2">
                    <span className="text-teal-400">✓</span>
                    <span>Everything in Pro</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-teal-400">✓</span>
                    <span>Team collaboration</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-teal-400">✓</span>
                    <span>Custom integrations</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-teal-400">✓</span>
                    <span>Dedicated support</span>
                  </li>
                </ul>
                <Button className="w-full bg-gray-800 hover:bg-gray-700 text-white">Get started</Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold font-[family-name:var(--font-heading)] text-center mb-12">
            Frequently asked questions
          </h2>
          <div className="space-y-8">
            <div>
              <h3 className="text-lg font-semibold font-[family-name:var(--font-heading)] mb-2">
                Is my API specification kept private?
              </h3>
              <p className="text-gray-300">
                Yes, your specs are processed securely and never stored on our servers. All data is deleted immediately
                after processing.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold font-[family-name:var(--font-heading)] mb-2">
                Which OpenAPI versions are supported?
              </h3>
              <p className="text-gray-300">
                SpecMint supports both OpenAPI 3.0 and 3.1 specifications, including all major features and extensions.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold font-[family-name:var(--font-heading)] mb-2">
                What programming languages are supported?
              </h3>
              <p className="text-gray-300">
                We generate tests for Java (JUnit/REST Assured), Python (pytest), Node.js (Jest), and export to Postman
                collections.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold font-[family-name:var(--font-heading)] mb-2">
                Can I use this in my CI/CD pipeline?
              </h3>
              <p className="text-gray-300">
                Generated tests are designed to integrate seamlessly with popular CI/CD platforms like GitHub Actions,
                Jenkins, and GitLab CI.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold font-[family-name:var(--font-heading)] mb-2">
                Do you offer self-hosted or enterprise solutions?
              </h3>
              <p className="text-gray-300">
                Yes, we offer enterprise solutions with self-hosting options, custom integrations, and dedicated
                support. Contact us for details.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-4 md:mb-0">
              <h3 className="text-xl font-bold font-[family-name:var(--font-heading)] text-teal-400">SpecMint</h3>
            </div>
            <div className="flex flex-wrap gap-6 text-sm">
              <a href="#docs" className="text-gray-400 hover:text-white transition-colors">
                Docs
              </a>
              <a href="#changelog" className="text-gray-400 hover:text-white transition-colors">
                Changelog
              </a>
              <a href="#github" className="text-gray-400 hover:text-white transition-colors">
                GitHub
              </a>
              <a href="#security" className="text-gray-400 hover:text-white transition-colors">
                Security
              </a>
              <a href="#contact" className="text-gray-400 hover:text-white transition-colors">
                Contact
              </a>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-gray-800 text-center text-gray-400 text-sm">
            © 2024 SpecMint. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}

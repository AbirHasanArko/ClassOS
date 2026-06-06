import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Github, Linkedin, Mail, Code, Server, Cpu, Database, Fingerprint, Camera } from 'lucide-react';

export const AboutPage = () => {
  const developers = [
    {
      name: "Abir Hasan Arko",
      email: "abirhasanarko2004@gmail.com",
      github: "https://github.com/AbirHasanArko",
      linkedin: "https://www.linkedin.com/in/abirhasanarko/",
      role: "Lead Developer"
    },
    {
      name: "Md Shomik Shahriar",
      github: "https://github.com/Hapi-Guy",
      linkedin: "https://www.linkedin.com/in/shomik101001/",
      role: "Developer"
    }
  ];

  const features = [
    { icon: Camera, title: "Face Recognition", desc: "AI-powered realtime face detection using YOLOv8 and dlib for instant attendance." },
    { icon: Fingerprint, title: "Fingerprint Scanning", desc: "Hardware integration with R307 fingerprint sensor via serial communication for secondary verification." },
    { icon: Server, title: "FastAPI Backend", desc: "High-performance asynchronous Python backend with WebSocket support for live updates." },
    { icon: Database, title: "PostgreSQL Data", desc: "Robust relational data modeling for users, courses, enrollments, and attendance logs." },
    { icon: Cpu, title: "Edge Computing", desc: "Optimized to run directly on a Raspberry Pi 5 orchestrating the camera, GPIO, and database." },
    { icon: Code, title: "React Dashboard", desc: "Beautiful, responsive UI built with Vite, React, and Tailwind CSS." }
  ];

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-10">
      {/* Header Section */}
      <div className="text-center space-y-4 pt-6">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-primary text-primary-foreground text-4xl font-bold mb-2 shadow-lg">
          C
        </div>
        <h1 className="text-4xl font-extrabold tracking-tight">About ClassOS</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          A smart, hardware-accelerated attendance management system designed for modern classrooms.
        </p>
      </div>

      {/* Project Info Section */}
      <Card className="border-primary/10 shadow-md">
        <CardHeader>
          <CardTitle className="text-2xl">The Project</CardTitle>
        </CardHeader>
        <CardContent className="prose prose-sm dark:prose-invert max-w-none text-muted-foreground">
          <p className="text-base leading-relaxed">
            ClassOS was built to solve the tedious and error-prone nature of manual attendance taking. By combining 
            computer vision, biometric hardware, and a modern web stack, it provides teachers with a completely 
            automated experience. The system runs entirely on the edge (Raspberry Pi), processing video feeds locally 
            to ensure student privacy and low latency, while exposing a rich web interface for administration and analytics.
          </p>
        </CardContent>
      </Card>

      {/* Features Grid */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight mb-4 px-1">Key Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((feat, idx) => (
            <Card key={idx} className="bg-card hover:bg-accent/5 transition-colors border border-border/50">
              <CardContent className="p-6">
                <feat.icon className="w-10 h-10 text-primary mb-4" />
                <h3 className="font-bold text-lg mb-2">{feat.title}</h3>
                <p className="text-sm text-muted-foreground">{feat.desc}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Developers Section */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight mb-4 px-1">Meet the Developers</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {developers.map((dev, idx) => (
            <Card key={idx} className="overflow-hidden border-border/50 shadow-sm">
              <div className="h-2 bg-primary w-full"></div>
              <CardContent className="p-6">
                <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                  <div>
                    <h3 className="text-xl font-bold">{dev.name}</h3>
                    <p className="text-sm font-medium text-primary mt-1">{dev.role}</p>
                  </div>
                  <div className="flex gap-2">
                    {dev.github && (
                      <a href={dev.github} target="_blank" rel="noreferrer" className="p-2 bg-muted hover:bg-primary hover:text-primary-foreground rounded-full transition-colors text-muted-foreground">
                        <Github className="w-5 h-5" />
                      </a>
                    )}
                    {dev.linkedin && (
                      <a href={dev.linkedin} target="_blank" rel="noreferrer" className="p-2 bg-muted hover:bg-primary hover:text-primary-foreground rounded-full transition-colors text-muted-foreground">
                        <Linkedin className="w-5 h-5" />
                      </a>
                    )}
                    {dev.email && (
                      <a href={`mailto:${dev.email}`} className="p-2 bg-muted hover:bg-primary hover:text-primary-foreground rounded-full transition-colors text-muted-foreground">
                        <Mail className="w-5 h-5" />
                      </a>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

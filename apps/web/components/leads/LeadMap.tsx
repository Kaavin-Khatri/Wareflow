"use client";

import React, { useEffect, useRef, useState } from "react";
import { LeadItem, getCategoryMetadata } from "./LeadInfoWindow";
import { MapPin, Navigation, Sparkles, ZoomIn, ZoomOut, Layers, RefreshCw } from "lucide-react";

export interface LeadMapProps {
  leads: LeadItem[];
  selectedLeadId?: string | null;
  onSelectLead: (lead: LeadItem) => void;
  center?: { lat: number; lng: number };
  radiusKm?: number;
  className?: string;
}

const DEFAULT_CENTER = { lat: 23.01185905490891, lng: 72.53806563827865 }; // Ahmedabad Hub
const DEFAULT_RADIUS_KM = 15;

export function LeadMap({
  leads,
  selectedLeadId,
  onSelectLead,
  center = DEFAULT_CENTER,
  radiusKm = DEFAULT_RADIUS_KM,
  className = "",
}: LeadMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const googleMapRef = useRef<any>(null);
  const markersRef = useRef<Map<string, any>>(new Map());
  const circleRef = useRef<any>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState(false);

  // Zoom level for fallback schematic view
  const [schematicZoom, setSchematicZoom] = useState(1);

  // Load Google Maps API script
  useEffect(() => {
    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

    if (!apiKey || typeof window === "undefined") {
      setMapError(true);
      return;
    }

    if ((window as any).google?.maps) {
      setMapLoaded(true);
      return;
    }

    const scriptId = "google-maps-script";
    if (document.getElementById(scriptId)) {
      const interval = setInterval(() => {
        if ((window as any).google?.maps) {
          setMapLoaded(true);
          clearInterval(interval);
        }
      }, 200);
      return () => clearInterval(interval);
    }

    const script = document.createElement("script");
    script.id = scriptId;
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places,geometry`;
    script.async = true;
    script.defer = true;
    script.onload = () => setMapLoaded(true);
    script.onerror = () => setMapError(true);
    document.head.appendChild(script);
  }, []);

  // Initialize Google Maps instance
  useEffect(() => {
    if (!mapLoaded || !mapContainerRef.current || !(window as any).google?.maps) return;

    try {
      const google = (window as any).google;

      // Dark luxury map styles tailored to liquid glass theme
      const darkMapStyles = [
        { elementType: "geometry", stylers: [{ color: "#0f172a" }] },
        { elementType: "labels.text.stroke", stylers: [{ color: "#0f172a" }] },
        { elementType: "labels.text.fill", stylers: [{ color: "#94a3b8" }] },
        {
          featureType: "administrative.locality",
          elementType: "labels.text.fill",
          stylers: [{ color: "#cbd5e1" }],
        },
        { featureType: "poi", elementType: "labels.text.fill", stylers: [{ color: "#64748b" }] },
        { featureType: "poi.park", elementType: "geometry", stylers: [{ color: "#132338" }] },
        { featureType: "road", elementType: "geometry", stylers: [{ color: "#1e293b" }] },
        { featureType: "road", elementType: "geometry.stroke", stylers: [{ color: "#0f172a" }] },
        {
          featureType: "road.highway",
          elementType: "geometry",
          stylers: [{ color: "#334155" }],
        },
        { featureType: "transit", elementType: "geometry", stylers: [{ color: "#1e293b" }] },
        { featureType: "water", elementType: "geometry", stylers: [{ color: "#020617" }] },
      ];

      const map = new google.maps.Map(mapContainerRef.current, {
        center: center,
        zoom: 12,
        styles: darkMapStyles,
        disableDefaultUI: false,
        zoomControl: true,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: true,
      });

      googleMapRef.current = map;

      // Warehouse Hub Circle
      circleRef.current = new google.maps.Circle({
        strokeColor: "#7C3AED",
        strokeOpacity: 0.8,
        strokeWeight: 2,
        fillColor: "#7C3AED",
        fillOpacity: 0.08,
        map: map,
        center: center,
        radius: radiusKm * 1000,
      });

      // Warehouse Center Marker
      new google.maps.Marker({
        position: center,
        map: map,
        title: "WareFlow Hub",
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 8,
          fillColor: "#7C3AED",
          fillOpacity: 1,
          strokeColor: "#ffffff",
          strokeWeight: 2,
        },
      });
    } catch (err) {
      console.warn("Failed to initialize Google Maps:", err);
      setMapError(true);
    }
  }, [mapLoaded, center, radiusKm]);

  // Update Markers on Google Map
  useEffect(() => {
    if (!mapLoaded || !googleMapRef.current || !(window as any).google?.maps) return;

    const google = (window as any).google;
    const currentMarkers = markersRef.current;

    // Clear removed markers
    currentMarkers.forEach((marker, id) => {
      if (!leads.some((l) => l.id === id)) {
        marker.setMap(null);
        currentMarkers.delete(id);
      }
    });

    // Add or update markers
    leads.forEach((lead) => {
      if (!lead.lat || !lead.lng) return;

      const position = { lat: lead.lat, lng: lead.lng };
      const catMeta = getCategoryMetadata(lead.category);

      let marker = currentMarkers.get(lead.id);

      if (!marker) {
        // Create custom SVG Pin
        const pinColor = catMeta.color;
        const isNew = lead.is_new;

        const pinSvg = `
          <svg xmlns="http://www.w3.org/2000/svg" width="36" height="44" viewBox="0 0 36 44">
            <defs>
              <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="#000000" flood-opacity="0.6"/>
              </filter>
            </defs>
            <path d="M18 0C8.06 0 0 8.06 0 18c0 13.5 18 26 18 26s18-12.5 18-26C36 8.06 27.94 0 18 0z" 
                  fill="${pinColor}" 
                  stroke="${isNew ? "#F59E0B" : "#ffffff"}" 
                  stroke-width="${isNew ? "3" : "1.5"}" 
                  filter="url(#shadow)"/>
            <circle cx="18" cy="18" r="7" fill="#ffffff"/>
            ${
              isNew
                ? `<circle cx="28" cy="8" r="6" fill="#F59E0B" stroke="#ffffff" stroke-width="1.5"/>`
                : ""
            }
          </svg>
        `;

        marker = new google.maps.Marker({
          position: position,
          map: googleMapRef.current,
          title: lead.name,
          icon: {
            url: `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(pinSvg)}`,
            scaledSize: new google.maps.Size(36, 44),
            anchor: new google.maps.Point(18, 44),
          },
        });

        marker.addListener("click", () => {
          onSelectLead(lead);
        });

        currentMarkers.set(lead.id, marker);
      }
    });
  }, [leads, mapLoaded, onSelectLead]);

  // Pan to selected lead on Google Map
  useEffect(() => {
    if (!selectedLeadId || !googleMapRef.current) return;
    const selected = leads.find((l) => l.id === selectedLeadId);
    if (selected && selected.lat && selected.lng) {
      googleMapRef.current.panTo({ lat: selected.lat, lng: selected.lng });
      googleMapRef.current.setZoom(14);
    }
  }, [selectedLeadId, leads]);

  // If map script cannot load or is offline, render the interactive spatial schematic
  return (
    <div
      className={`relative w-full h-full min-h-[450px] rounded-2xl overflow-hidden border border-[var(--glass-border)] bg-[var(--surface-overlay)] ${className}`}
    >
      {/* Real Google Maps Container */}
      {!mapError && (
        <div
          ref={mapContainerRef}
          data-testid="google-map-container"
          className="w-full h-full min-h-[450px]"
        />
      )}

      {/* Fallback Spatial Radar Canvas (For Offline, Tests, or Missing Key) */}
      {mapError && (
        <div
          data-testid="schematic-map-fallback"
          className="relative w-full h-full min-h-[450px] bg-gradient-to-b from-[#0b1120] to-[#020617] flex flex-col items-center justify-center p-6 overflow-hidden select-none"
        >
          {/* Subtle Grid Matrix Background */}
          <div
            className="absolute inset-0 opacity-20 pointer-events-none"
            style={{
              backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255,255,255,0.2) 1px, transparent 0)`,
              backgroundSize: "24px 24px",
            }}
          />

          {/* Territory Radar Viewport */}
          <div
            className="relative w-full max-w-[500px] aspect-square rounded-full border border-violet-500/20 bg-violet-950/10 flex items-center justify-center transition-transform duration-300"
            style={{ transform: `scale(${schematicZoom})` }}
          >
            {/* Concentric distance range rings */}
            <div className="absolute w-[75%] aspect-square rounded-full border border-violet-500/15 border-dashed" />
            <div className="absolute w-[50%] aspect-square rounded-full border border-violet-500/20" />
            <div className="absolute w-[25%] aspect-square rounded-full border border-violet-500/30" />

            {/* Central Business Warehouse Hub */}
            <div className="relative z-10 w-8 h-8 rounded-full bg-[var(--accent)] text-white flex items-center justify-center shadow-[0_0_24px_var(--accent-glow)] border-2 border-white">
              <Navigation className="w-4 h-4 transform -rotate-45" />
            </div>

            {/* Render Pins inside schematic radius */}
            {leads.map((lead, idx) => {
              const catMeta = getCategoryMetadata(lead.category);
              const isSelected = lead.id === selectedLeadId;

              // Calculate relative spatial offset from center coordinates
              const latDiff = (lead.lat ?? center.lat) - center.lat;
              const lngDiff = (lead.lng ?? center.lng) - center.lng;

              // Project into percentage coordinates (-45% to +45%)
              const xPercent = Math.max(-42, Math.min(42, lngDiff * 450));
              const yPercent = Math.max(-42, Math.min(42, -latDiff * 450));

              return (
                <button
                  key={lead.id}
                  type="button"
                  data-testid={`map-pin-${lead.id}`}
                  onClick={() => onSelectLead(lead)}
                  style={{
                    left: `calc(50% + ${xPercent}%)`,
                    top: `calc(50% + ${yPercent}%)`,
                  }}
                  className={`absolute -translate-x-1/2 -translate-y-1/2 group cursor-pointer z-20 transition-all ${
                    isSelected ? "scale-125 z-30" : "hover:scale-115"
                  }`}
                  aria-label={`${lead.name} (${catMeta.label})`}
                >
                  <div className="relative flex flex-col items-center">
                    {/* Glowing Pulse Ring for New Leads */}
                    {lead.is_new && (
                      <span className="absolute -inset-2 rounded-full bg-amber-400/40 animate-ping pointer-events-none" />
                    )}

                    {/* Pin Bubble */}
                    <div
                      className={`w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold border-2 shadow-lg transition-transform ${
                        isSelected
                          ? "ring-4 ring-white shadow-[0_0_20px_rgba(255,255,255,0.8)]"
                          : ""
                      }`}
                      style={{
                        backgroundColor: catMeta.color,
                        borderColor: lead.is_new ? "#F59E0B" : "#ffffff",
                      }}
                    >
                      <MapPin className="w-3.5 h-3.5" />
                    </div>

                    {/* New Badge Pill */}
                    {lead.is_new && (
                      <span className="absolute -top-2.5 -right-2 px-1 py-0.2 rounded-full text-[8px] font-black uppercase tracking-wider bg-amber-500 text-black shadow-sm">
                        New
                      </span>
                    )}

                    {/* Name Tooltip on hover/selected */}
                    <div
                      className={`absolute top-full mt-1.5 px-2 py-0.5 rounded-md text-[10px] font-semibold whitespace-nowrap bg-black/90 text-white border border-white/10 shadow-xl pointer-events-none transition-opacity ${
                        isSelected ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                      }`}
                    >
                      {lead.name}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Schematic Controls & Disclaimer */}
          <div className="absolute top-4 left-4 z-20 flex items-center gap-2">
            <span className="text-[11px] font-mono px-2.5 py-1 rounded-lg bg-black/60 text-[var(--text-muted)] border border-white/10 backdrop-blur-md flex items-center gap-1.5">
              <Layers className="w-3 h-3 text-[var(--accent)]" />
              Radius: {radiusKm} km ({leads.length} shops)
            </span>
          </div>

          <div className="absolute bottom-4 right-4 z-20 flex items-center gap-1.5 bg-black/60 p-1.5 rounded-xl border border-white/10 backdrop-blur-md">
            <button
              type="button"
              onClick={() => setSchematicZoom((z) => Math.min(1.6, z + 0.15))}
              aria-label="Zoom In"
              className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-white hover:bg-white/10"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => setSchematicZoom((z) => Math.max(0.7, z - 0.15))}
              aria-label="Zoom Out"
              className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-white hover:bg-white/10"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => setSchematicZoom(1)}
              aria-label="Reset Zoom"
              className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-white hover:bg-white/10"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Map Legend Overlay */}
      <div className="absolute bottom-4 left-4 z-10 hidden sm:flex items-center gap-2 p-2 rounded-xl bg-black/70 backdrop-blur-md border border-white/10 text-[10px] font-medium text-slate-300">
        <div className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" />
          <span>Gruh Udyog</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-[#F43F5E]" />
          <span>Snacks</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]" />
          <span>Kirana</span>
        </div>
        <div className="flex items-center gap-1 pl-1 border-l border-white/20">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400 ring-2 ring-amber-400/50 animate-pulse" />
          <span className="font-bold text-amber-300">New Shop</span>
        </div>
      </div>
    </div>
  );
}


import { VideoProject, Clip, ViralShort, TextOverlay } from '../types';

export const parseEDLXml = (xmlString: string, metadata?: any): VideoProject => {
  const parser = new DOMParser();
  const xmlDoc = parser.parseFromString(xmlString, "text/xml");

  const projectNode = xmlDoc.querySelector('project');
  const projectName = projectNode?.getAttribute('name') || 'Untitled Project';

  // Create a lookup map if metadata exists (it's the 'timeline' array from analysis.json)
  const metaMap = new Map();
  if (metadata?.timeline) {
    metadata.timeline.forEach((item: any) => metaMap.set(String(item.id), item));
  }

  // Helper to parse color grading
  const parseColorGrading = (parent: Element | null) => {
    if (!parent) return undefined;
    const node = parent.querySelector('color_grading');
    if (!node) return undefined;

    return {
      temperature: parseFloat(node.querySelector('temperature')?.textContent || '5600'),
      exposure: parseFloat(node.querySelector('exposure')?.textContent || '0'),
      contrast: parseFloat(node.querySelector('contrast')?.textContent || '0'),
      saturation: parseFloat(node.querySelector('saturation')?.textContent || '100'),
      filterStrength: parseFloat(node.querySelector('filter_strength')?.textContent || '100'),
    };
  };

  // Handle global settings
  const globalSettingsNode = xmlDoc.querySelector('global_settings');
  const filterSuggestion = globalSettingsNode?.querySelector('filter_suggestion')?.textContent ||
    xmlDoc.querySelector('filter_suggestion')?.textContent ||
    'Natural Grade';

  const globalColorGrading = parseColorGrading(globalSettingsNode) || parseColorGrading(xmlDoc.documentElement);

  const clips: Clip[] = Array.from(xmlDoc.querySelectorAll('clip')).map(node => {
    const id = node.getAttribute('id') || Math.random().toString(36).substr(2, 9);
    const meta = metaMap.get(id);

    // Prefer metadata start/end if available, otherwise XML attribute, otherwise 0
    // Note: meta.start/end are numbers, XML attrs are strings
    let start = meta ? meta.start : parseFloat(node.getAttribute('start') || '0');
    let end = meta ? meta.end : parseFloat(node.getAttribute('end') || '0');

    // Check for invalid numbers (e.g. NaN if parsing "...")
    if (isNaN(start)) start = 0;
    if (isNaN(end)) end = 0;

    let xmlDuration = parseFloat(node.getAttribute('duration') || '0');
    if (isNaN(xmlDuration)) xmlDuration = 0;

    // If we don't have a valid end time but we have a duration from XML, use it
    if ((end === 0 || end <= start) && xmlDuration > 0) {
      end = start + xmlDuration;
    }

    // Calculate duration
    let duration = end - start;
    if (duration <= 0) {
      if (xmlDuration > 0) {
        duration = xmlDuration;
        end = start + duration;
      } else {
        // Fallback for visual mock only if absolutely no data found
        // This prevents 0 duration clips breaking the timeline
        duration = 5;
      }
    }

    return {
      id,
      source: node.getAttribute('source') || 'Unknown Source',
      keep: node.getAttribute('keep') === 'true',
      reason: node.getAttribute('reason') || 'No reason provided',
      start,
      end,
      emotionScore: Math.floor(Math.random() * 40) + 60,
      duration,
      colorGrading: parseColorGrading(node)
    };
  });

  const viralShorts: ViralShort[] = Array.from(xmlDoc.querySelectorAll('short')).map(node => ({
    title: node.querySelector('title')?.textContent || 'Untitled Short',
    description: node.querySelector('description')?.textContent || 'No description',
    clipIds: node.querySelector('clip_ids')?.textContent?.split(',').map(s => s.trim()).filter(Boolean) || []
  }));

  const overlays: TextOverlay[] = Array.from(xmlDoc.querySelectorAll('overlays text')).map(node => {
    const id = node.getAttribute('id') || Math.random().toString(36).substr(2, 9);
    const content = node.getAttribute('content') || '';
    const start = parseFloat(node.getAttribute('start') || '0');
    const duration = parseFloat(node.getAttribute('duration') || '0');
    const style = node.getAttribute('style') || 'pop';
    const origin = (node.getAttribute('origin') as 'ai' | 'manual') || 'manual';

    // New attributes
    const sizeAttr = node.getAttribute('size');
    const fontSize = sizeAttr ? parseFloat(sizeAttr) : undefined;

    const xAttr = node.getAttribute('x');
    const positionX = xAttr ? parseFloat(xAttr) : undefined;

    const yAttr = node.getAttribute('y');
    const positionY = yAttr ? parseFloat(yAttr) : undefined;

    const textColor = node.getAttribute('color') || undefined;
    const fontFamily = node.getAttribute('font') || undefined;

    return {
      id,
      content,
      start: isNaN(start) ? 0 : start,
      duration: isNaN(duration) ? 2.0 : duration,
      style,
      origin,
      fontSize,
      positionX,
      positionY,
      textColor,
      fontFamily
    };
  });

  return {
    name: projectName,
    globalSettings: {
      filterSuggestion,
      colorGrading: globalColorGrading
    },
    edl: clips,
    viralShorts,
    overlays
  };
};

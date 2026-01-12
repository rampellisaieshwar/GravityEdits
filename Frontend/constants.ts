
export const MOCK_XML_EDL = `
<project name="Test_Project">
  <edl>
    <clip id="1" source="WTN1.mp4" keep="true" reason="Intro" />
    <clip id="2" source="WTN1.mp4" keep="true" reason="Relevant info" />
    <clip id="3" source="WTN1.mp4" keep="true" reason="Surprise element" />
    <clip id="4" source="WTN1.mp4" keep="true" reason="Positive tone" />
    <clip id="5" source="WTN1.mp4" keep="false" reason="Not relevant to main topic" />
    <clip id="6" source="WTN1.mp4" keep="true" reason="Relevant info" />
    <clip id="7" source="WTN1.mp4" keep="true" reason="Sad tone" />
    <clip id="8" source="WTN1.mp4" keep="true" reason="Relevant info" />
    <clip id="9" source="WTN1.mp4" keep="true" reason="Happy tone" />
    <clip id="10" source="WTN1.mp4" keep="true" reason="Relevant info" />
    <clip id="11" source="WTN1.mp4" keep="true" reason="Happy tone" />
    <clip id="12" source="WTN1.mp4" keep="true" reason="Relevant info" />
    <clip id="13" source="WTN1.mp4" keep="false" reason="Not relevant to main topic" />
    <clip id="14" source="WTN1.mp4" keep="true" reason="Fear tone" />
    <clip id="15" source="WTN1.mp4" keep="true" reason="Relevant info" />
    <clip id="16" source="WTN1.mp4" keep="false" reason="Not relevant to main topic" />
    <clip id="17" source="WTN1.mp4" keep="true" reason="Sad tone" />
    <clip id="18" source="WTN1.mp4" keep="true" reason="Relevant info" />
    <clip id="19" source="WTN1.mp4" keep="false" reason="Not relevant to main topic" />
    <clip id="20" source="WTN1.mp4" keep="true" reason="Sad tone" />
    <clip id="21" source="WTN1.mp4" keep="false" reason="Not relevant to main topic" />
    <clip id="22" source="WTN2.mp4" keep="true" reason="Relevant info" />
    <clip id="23" source="WTN2.mp4" keep="true" reason="Sad tone" />
    <clip id="24" source="WTN2.mp4" keep="false" reason="Not relevant to main topic" />
    <clip id="25" source="WTN2.mp4" keep="true" reason="Relevant info" />
    <clip id="26" source="WTN2.mp4" keep="true" reason="Sad tone" />
    <clip id="27" source="WTN2.mp4" keep="false" reason="Not relevant to main topic" />
    <clip id="28" source="WTN2.mp4" keep="true" reason="Happy tone" />
    <clip id="29" source="WTN2.mp4" keep="false" reason="Not relevant to main topic" />
    <clip id="30" source="WTN2.mp4" keep="true" reason="Neutral tone" />
    <clip id="31" source="WTN3.mp4" keep="true" reason="Relevant info" />
    <clip id="32" source="WTN3.mp4" keep="false" reason="Not relevant to main topic" />
    <clip id="33" source="WTN3.mp4" keep="true" reason="Fear tone" />
    <clip id="34" source="WTN3.mp4" keep="false" reason="Not relevant to main topic" />
    <clip id="35" source="WTN3.mp4" keep="true" reason="Surprise element" />
    <clip id="36" source="WTN3.mp4" keep="true" reason="Happy tone" />
    <clip id="37" source="WTN3.mp4" keep="false" reason="Not relevant to main topic" />
    <clip id="38" source="WTN3.mp4" keep="true" reason="Fear tone" />
    <clip id="39" source="WTN3.mp4" keep="false" reason="Not relevant to main topic" />
    <clip id="40" source="WTN3.mp4" keep="true" reason="Angry tone" />
  </edl>
  <viral_shorts>
    <short id="1" original_clip_id="5" reason="Funny" />
    <short id="2" original_clip_id="28" reason="Happy" />
    <short id="3" original_clip_id="36" reason="Surprise" />
  </viral_shorts>
</project>
`;

export const THEME = {
  bg: '#121212',
  panel: '#1E1E1E',
  border: '#2A2A2A',
  accentKeep: '#3B82F6',
  accentReject: '#EF4444',
  accentViral: '#F59E0B',
  textMain: '#E0E0E0',
  textDim: '#888888',
};

export const API_BASE_URL = 'http://127.0.0.1:8000';

"""
Tests for APRS Packet Parser

Tests cover:
- Uncompressed position parsing
- Compressed position parsing (Base91)
- Mic-E encoded position parsing
- Edge cases and error handling
"""

import pytest
from app.aprs.parser import APRSParser, APRSPosition


@pytest.fixture
def parser():
    return APRSParser()


class TestUncompressedPosition:
    """Tests for standard uncompressed APRS position format"""
    
    def test_basic_position_no_timestamp(self, parser):
        """Parse basic position without timestamp (!format)"""
        packet = "W1ABC>APRS,WIDE1-1:!4221.61N/07103.53W-Mobile"
        result = parser.parse(packet)
        
        assert result is not None
        assert result.callsign == "W1ABC"
        assert pytest.approx(result.latitude, 0.01) == 42.36
        assert pytest.approx(result.longitude, 0.01) == -71.06
        assert result.symbol_table == "/"
        assert result.symbol_code == "-"
        assert "Mobile" in result.comment
    
    def test_position_with_timestamp(self, parser):
        """Parse position with timestamp (@format)"""
        packet = "W1ABC>APRS:@092345z4221.61N/07103.53W-Test"
        result = parser.parse(packet)
        
        assert result is not None
        assert result.callsign == "W1ABC"
        assert pytest.approx(result.latitude, 0.01) == 42.36
        assert pytest.approx(result.longitude, 0.01) == -71.06
    
    def test_position_south_east(self, parser):
        """Parse position in southern/eastern hemisphere"""
        packet = "VK2ABC>APRS:!3352.00S/15112.00E-Sydney"
        result = parser.parse(packet)
        
        assert result is not None
        assert result.latitude < 0  # South
        assert result.longitude > 0  # East
        assert pytest.approx(result.latitude, 0.01) == -33.87
        assert pytest.approx(result.longitude, 0.01) == 151.20
    
    def test_position_with_altitude(self, parser):
        """Parse position with altitude in comment"""
        packet = "W1ABC>APRS:!4221.61N/07103.53W-/A=001000"
        result = parser.parse(packet)
        
        assert result is not None
        assert result.altitude_m is not None
        assert pytest.approx(result.altitude_m, 1) == 304.8  # 1000ft in meters
    
    def test_position_with_course_speed(self, parser):
        """Parse position with course/speed in comment"""
        packet = "W1ABC>APRS:!4221.61N/07103.53W-090/055"
        result = parser.parse(packet)
        
        assert result is not None
        assert result.course_deg == 90.0
        assert result.speed_knots == 55.0
    
    def test_messaging_position_format(self, parser):
        """Parse position with messaging enabled (=format)"""
        packet = "W1ABC>APRS:=4221.61N/07103.53W-Test"
        result = parser.parse(packet)
        
        assert result is not None
        assert result.callsign == "W1ABC"


class TestCompressedPosition:
    """Tests for compressed APRS position format (Base91)"""
    
    def test_compressed_position(self, parser):
        """Parse compressed position format"""
        # Compressed format: /YYYYXXXX$csT
        # This represents approximately 49.5°N, 72.75°W
        packet = "W1ABC>APRS:!/5L!!<*e7>7P["
        result = parser.parse(packet)
        
        assert result is not None
        assert result.callsign == "W1ABC"
        # Compressed positions decode to specific values
        assert result.latitude is not None
        assert result.longitude is not None
    
    def test_compressed_with_altitude(self, parser):
        """Parse compressed position with altitude encoding"""
        # Altitude encoding uses different compression type byte
        packet = "W1ABC>APRS:!/5L!!<*e7S]S"
        result = parser.parse(packet)
        
        assert result is not None


class TestMicEPosition:
    """Tests for Mic-E encoded position format"""
    
    def test_basic_mic_e(self, parser):
        """Parse basic Mic-E position"""
        # Mic-E encodes position in destination address
        # Destination "T4RXYY" encodes latitude ~42.36N
        packet = "W1ABC>T4RXYY:`l!lP->/]\"4V}"
        result = parser.parse(packet)
        
        assert result is not None
        assert result.callsign == "W1ABC"
    
    def test_mic_e_with_ssid(self, parser):
        """Parse Mic-E from station with SSID"""
        packet = "W1ABC-9>S4TPYY:`l\"el!>/]\"4K}"
        result = parser.parse(packet)
        
        assert result is not None
        assert result.callsign == "W1ABC-9"


class TestInvalidPackets:
    """Tests for error handling with invalid packets"""
    
    def test_empty_packet(self, parser):
        """Empty packet should return None"""
        assert parser.parse("") is None
        assert parser.parse("   ") is None
    
    def test_no_source(self, parser):
        """Packet without > delimiter should return None"""
        assert parser.parse("APRS:!4221.61N/07103.53W-") is None
    
    def test_no_info_field(self, parser):
        """Packet without : delimiter should return None"""
        assert parser.parse("W1ABC>APRS") is None
    
    def test_non_position_packet(self, parser):
        """Status message (not position) should return None"""
        # Status packets start with '>'
        result = parser.parse("W1ABC>APRS:>Status message here")
        assert result is None
    
    def test_message_packet(self, parser):
        """Message packet should return None"""
        # Message packets start with ':'
        result = parser.parse("W1ABC>APRS::W2XYZ    :Hello{001")
        assert result is None
    
    def test_telemetry_packet(self, parser):
        """Telemetry packet should return None"""
        # Telemetry packets start with 'T'
        result = parser.parse("W1ABC>APRS:T#001,100,200,300,400,500,00000000")
        assert result is None
    
    def test_malformed_position(self, parser):
        """Malformed position should return None"""
        # Position too short
        result = parser.parse("W1ABC>APRS:!4221")
        assert result is None


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""
    
    def test_callsign_with_ssid(self, parser):
        """Callsign with SSID should be preserved"""
        packet = "W1ABC-15>APRS:!4221.61N/07103.53W-"
        result = parser.parse(packet)
        
        assert result is not None
        assert result.callsign == "W1ABC-15"
    
    def test_long_path(self, parser):
        """Packet with long digipeater path"""
        packet = "W1ABC>APRS,WIDE1-1,WIDE2-2,qAR,W2XYZ:!4221.61N/07103.53W-"
        result = parser.parse(packet)
        
        assert result is not None
        assert result.callsign == "W1ABC"
    
    def test_raw_packet_preserved(self, parser):
        """Raw packet should be stored in result"""
        packet = "W1ABC>APRS:!4221.61N/07103.53W-Test"
        result = parser.parse(packet)
        
        assert result is not None
        assert result.raw_packet == packet
    
    def test_whitespace_handling(self, parser):
        """Leading/trailing whitespace should be handled"""
        packet = "  W1ABC>APRS:!4221.61N/07103.53W-  "
        result = parser.parse(packet)
        
        assert result is not None
        assert result.callsign == "W1ABC"
    
    def test_special_symbols(self, parser):
        """Various APRS symbols should be parsed"""
        # Car symbol: /k
        packet = "W1ABC>APRS:!4221.61N/07103.53Wk"
        result = parser.parse(packet)
        
        assert result is not None
        assert result.symbol_code == "k"
        
        # House symbol: /-
        packet2 = "W1ABC>APRS:!4221.61N/07103.53W-"
        result2 = parser.parse(packet2)
        
        assert result2 is not None
        assert result2.symbol_code == "-"


class TestRealWorldPackets:
    """Tests with real-world APRS packet examples"""
    
    def test_kenwood_th_d74(self, parser):
        """Packet from Kenwood TH-D74 handheld"""
        packet = "N1ABC-7>APTT4,WIDE1-1,WIDE2-1,qAR,W1XYZ-1:!4235.29N/07118.23W>/A=000328"
        result = parser.parse(packet)
        
        assert result is not None
        assert result.callsign == "N1ABC-7"
        assert result.altitude_m is not None
    
    def test_aprsis_position(self, parser):
        """Position received via APRS-IS"""
        packet = "W1ABC-9>APRS,TCPIP*,qAC,T2SOCAL:!4221.61N/07103.53W-PHG2360/Digi"
        result = parser.parse(packet)
        
        assert result is not None
        assert "PHG2360" in result.comment or "Digi" in result.comment


# Pydantic model tests
class TestAPRSPositionDataclass:
    """Tests for APRSPosition dataclass"""
    
    def test_default_values(self):
        """Test default values for optional fields"""
        pos = APRSPosition(
            callsign="W1ABC",
            latitude=42.0,
            longitude=-71.0
        )
        
        assert pos.symbol_table == "/"
        assert pos.symbol_code == "k"
        assert pos.comment is None
        assert pos.altitude_m is None
        assert pos.speed_knots is None
        assert pos.course_deg is None
        assert pos.raw_packet == ""
    
    def test_full_position(self):
        """Test position with all fields populated"""
        pos = APRSPosition(
            callsign="W1ABC-9",
            latitude=42.36,
            longitude=-71.06,
            symbol_table="/",
            symbol_code="k",
            comment="Mobile",
            altitude_m=100.0,
            speed_knots=55.0,
            course_deg=180.0,
            raw_packet="W1ABC-9>APRS:!..."
        )
        
        assert pos.callsign == "W1ABC-9"
        assert pos.latitude == 42.36
        assert pos.altitude_m == 100.0

"""Onvif SOAP message definitions"""


# System & service requests

GET_SYSTEM_DATETIME = """
<GetSystemDateAndTime xmlns="{OVF_DEVICE}"/>
"""

GET_CAPABILITIES = """
<GetCapabilities xmlns="{OVF_DEVICE}"><Category>All</Category></GetCapabilities>
"""

GET_SERVICE_CAPABILITIES = """
<GetServiceCapabilities xmlns="{OVF_DEVICE}"></GetServiceCapabilities>
"""

GET_SERVICES = """
<GetServices xmlns="{OVF_DEVICE}"><IncludeCapability>false</IncludeCapability></GetServices>
"""

GET_PROFILES = """
<GetProfiles xmlns="{OVF_MEDIA}"></GetProfiles>
"""

GET_DEVICE_INFO = """
<GetDeviceInformation xmlns="{OVF_DEVICE}"></GetDeviceInformation>
"""

GET_NODE = """
<GetNode xmlns="{OVF_PTZ}">
    <NodeToken>{node_token}</NodeToken>
</GetNode>
"""


# Movements

RELATIVE_MOVE = """
<RelativeMove xmlns="{OVF_PTZ}">{profile}
    <ProfileToken>{profile_token}</ProfileToken>
    <Translation>
        <PanTilt x="{x}" y="{y}" space="{OVF_PTS_TGS}" xmlns="{OVF_SCHEMA}"/>
    </Translation>
    <Speed>
        <PanTilt x="{xspeed}" y="{yspeed}" space="{OVF_PTS_GSS}" xmlns="{OVF_SCHEMA}"/>
    </Speed>
</RelativeMove>
"""

RELATIVE_MOVE_ZOOM = """
<RelativeMove xmlns="{OVF_PTZ}">{profile}
    <ProfileToken>{profile_token}</ProfileToken>
    <Translation>
        <Zoom x="{z}" space="{OVF_ZS_TGS}" xmlns="{OVF_SCHEMA}"/>
    </Translation>
    <Speed>
        <Zoom x="{zspeed}" space="{OVF_ZS_ZGSS}" xmlns="{OVF_SCHEMA}"/>
    </Speed>
</RelativeMove>
"""

ABSOLUTE_MOVE = """
<AbsoluteMove xmlns="{OVF_PTZ}">{profile}
    <Position>
        <ProfileToken>{profile_token}</ProfileToken>
        <PanTilt x="{x}" y="{y}" space="{OVF_PTS_PGS}" xmlns="{OVF_SCHEMA}"/>
        <Zoom x="{z}" space="{OVF_ZS_PGS}" xmlns="{OVF_SCHEMA}"/>
    </Position>
</AbsoluteMove>
"""

CONTINUOUS_MOVE = """
<ContinuousMove xmlns="{OVF_PTZ}">{profile}
    <ProfileToken>{profile_token}</ProfileToken>
    <Velocity>
        <PanTilt x="{x}" y="{y}" space="{OVF_PTS_VGS}" xmlns="{OVF_SCHEMA}"/>
    </Velocity>
</ContinuousMove>
"""

STOP = """
<Stop xmlns="{OVF_PTZ}">
    <ProfileToken>{profile_token}</ProfileToken>
    <PanTilt>{ptstop}</PanTilt>
    <Zoom>{zstop}</Zoom>
</Stop>
"""

CONTINUOUS_MOVE_ZOOM = """
<ContinuousMove xmlns="{OVF_PTZ}">{profile}
    <ProfileToken>{profile_token}</ProfileToken>
    <Velocity>
        <Zoom x="{z}" space="{OVF_ZS_VGS}" xmlns="{OVF_SCHEMA}"/>
    </Velocity>
</ContinuousMove>
"""


# Preset use and manipulation

SET_PRESET = """
    <SetPreset xmlns="{OVF_PTZ}">
        <ProfileToken>{profile_token}</ProfileToken>
        <PresetName>{preset_name}</PresetName>
    </SetPreset>
"""

GET_PRESETS = """
<GetPresets xmlns="{OVF_PTZ}">
    <ProfileToken>{profile_token}</ProfileToken>
</GetPresets>
"""

GOTO_PRESET = """
<GotoPreset xmlns="{OVF_PTZ}">
    <ProfileToken>{profile_token}</ProfileToken>
    <PresetToken>{preset_token}</PresetToken>
    <Speed>
        <PanTilt x="{xspeed}" y="{yspeed}" xmlns="{OVF_SCHEMA}"/>
        <Zoom x="{zspeed}" xmlns="{OVF_SCHEMA}"/>
    </Speed>
</GotoPreset>
"""

REMOVE_PRESET = """
<RemovePreset xmlns="{OVF_PTZ}">
    <ProfileToken>{profile_token}</ProfileToken>
    <PresetToken>{preset_token}</PresetToken>
</RemovePreset>
"""


# Video sources

GET_VIDEO_SOURCES = """
<GetVideoSources xmlns="{OVF_MEDIA}"/>
"""


# Video stream URI

GET_STREAM_URI = """
<GetStreamUri xmlns="{OVF_MEDIA}">
    <StreamSetup>
        <Stream xmlns="{OVF_SCHEMA}">RTP-Unicast</Stream>
        <Transport xmlns="{OVF_SCHEMA}">
            <Protocol>UDP</Protocol>
        </Transport>
    </StreamSetup>
    <ProfileToken>{profile_token}</ProfileToken>
</GetStreamUri>"""

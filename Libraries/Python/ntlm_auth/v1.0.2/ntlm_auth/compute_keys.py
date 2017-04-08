# This library is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see <http://www.gnu.org/licenses/> or <http://www.gnu.org/licenses/lgpl.txt>.

import binascii
import hashlib
import hmac
from ntlm_auth import des
from ntlm_auth.constants import NegotiateFlags

def _get_exchange_key_ntlm_v1(negotiate_flags, session_base_key, server_challenge, lm_challenge_response, lm_hash):
    """
    [MS-NLMP] v28.0 2016-07-14

    4.3.5.1 KXKEY
    Calculates the Key Exchange Key for NTLMv1 authentication. Used for signing and sealing messages

    @param negotiate_flags:
    @param session_base_key: A session key calculated from the user password challenge
    @param server_challenge: A random 8-byte response generated by the server in the CHALLENGE_MESSAGE
    @param lm_challenge_response: The LmChallengeResponse value computed in ComputeResponse
    @param lm_hash: The LMOWF computed in Compute Response
    @return key_exchange_key: The Key Exchange Key (KXKEY) used to sign and seal messages and compute the ExportedSessionKey
    """
    if negotiate_flags & NegotiateFlags.NTLMSSP_NEGOTIATE_EXTENDED_SESSIONSECURITY:
        key_exchange_key = hmac.new(session_base_key, server_challenge + lm_challenge_response[:8]).digest()
    elif negotiate_flags & NegotiateFlags.NTLMSSP_NEGOTIATE_LM_KEY:
        des_handler = des.DES(lm_hash[:7])
        first_des = des_handler.encrypt(lm_challenge_response[:8])
        des_handler = des.DES(lm_hash[7:8] + binascii.unhexlify('bdbdbdbdbdbdbd'))
        second_des = des_handler.encrypt(lm_challenge_response[:8])

        key_exchange_key = first_des + second_des
    elif negotiate_flags & NegotiateFlags.NTLMSSP_REQUEST_NON_NT_SESSION_KEY:
        key_exchange_key = lm_hash[:8] + b'\0' * 8
    else:
        key_exchange_key = session_base_key

    return key_exchange_key

def _get_exchange_key_ntlm_v2(session_base_key):
    """
    [MS-NLMP] v28.0 2016-07-14

    4.3.5.1 KXKEY
    Calculates the Key Exchange Key for NTLMv2 authentication. Used for signing and sealing messages.
    According to docs, 'If NTLM v2 is used, KeyExchangeKey MUST be set to the given 128-bit SessionBaseKey

    @param session_base_key: A session key calculated from the user password challenge
    @return key_exchange_key: The Key Exchange Key (KXKEY) used to sign and seal messages
    """
    return session_base_key

def get_sign_key(exported_session_key, magic_constant):
    """
    3.4.5.2 SIGNKEY

    @param exported_session_key: A 128-bit session key used to derive signing and sealing keys
    @param magic_constant: A constant value set in the MS-NLMP documentation (constants.SignSealConstants)
    @return sign_key: Key used to sign messages
    """

    sign_key = hashlib.md5(exported_session_key + magic_constant).digest()

    return sign_key

def get_seal_key(negotiate_flags, exported_session_key, magic_constant):
    """
    3.4.5.3. SEALKEY
    Main method to use to calculate the seal_key used to seal (encrypt) messages. This will determine
    the correct method below to use based on the compatibility flags set and should be called instead
    of the others

    @param exported_session_key: A 128-bit session key used to derive signing and sealing keys
    @param negotiate_flags: The negotiate_flags structure sent by the server
    @param magic_constant: A constant value set in the MS-NLMP documentation (constants.SignSealConstants)
    @return seal_key: Key used to seal messages
    """

    if negotiate_flags & NegotiateFlags.NTLMSSP_NEGOTIATE_EXTENDED_SESSIONSECURITY:
        seal_key = _get_seal_key_ntlm2(negotiate_flags, exported_session_key, magic_constant)
    elif negotiate_flags & NegotiateFlags.NTLMSSP_NEGOTIATE_LM_KEY:
        seal_key = _get_seal_key_ntlm1(negotiate_flags, exported_session_key)
    else:
        seal_key = exported_session_key

    return seal_key

def _get_seal_key_ntlm1(negotiate_flags, exported_session_key):
    """
    3.4.5.3 SEALKEY
    Calculates the seal_key used to seal (encrypt) messages. This for authentication where
    NTLMSSP_NEGOTIATE_EXTENDED_SESSIONSECURITY has not been negotiated. Will weaken the keys
    if NTLMSSP_NEGOTIATE_56 is not negotiated it will default to the 40-bit key

    @param negotiate_flags: The negotiate_flags structure sent by the server
    @param exported_session_key: A 128-bit session key used to derive signing and sealing keys
    @return seal_key: Key used to seal messages
    """
    if negotiate_flags & NegotiateFlags.NTLMSSP_NEGOTIATE_56:
        seal_key = exported_session_key[:7] + binascii.unhexlify('a0')
    else:
        seal_key = exported_session_key[:5] + binascii.unhexlify('e538b0')

    return seal_key

def _get_seal_key_ntlm2(negotiate_flags, exported_session_key, magic_constant):
    """
    3.4.5.3 SEALKEY
    Calculates the seal_key used to seal (encrypt) messages. This for authentication where
    NTLMSSP_NEGOTIATE_EXTENDED_SESSIONSECURITY has been negotiated. Will weaken the keys
    if NTLMSSP_NEGOTIATE_128 is not negotiated, will try NEGOTIATE_56 and then will default
    to the 40-bit key

    @param negotiate_flags: The negotiate_flags structure sent by the server
    @param exported_session_key: A 128-bit session key used to derive signing and sealing keys
    @param magic_constant: A constant value set in the MS-NLMP documentation (constants.SignSealConstants)
    @return seal_key: Key used to seal messages
    """
    if negotiate_flags & NegotiateFlags.NTLMSSP_NEGOTIATE_128:
        seal_key = exported_session_key
    elif negotiate_flags & NegotiateFlags.NTLMSSP_NEGOTIATE_56:
        seal_key = exported_session_key[:7]
    else:
        seal_key = exported_session_key[:5]

    seal_key = hashlib.md5(seal_key + magic_constant).digest()

    return seal_key
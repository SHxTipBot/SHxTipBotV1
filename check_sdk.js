const StellarSdk = require('stellar-sdk');
console.log('Stellar SDK version:', StellarSdk.VERSION || 'unknown');
try {
  const scval = StellarSdk.nativeToScVal('GAHO2LQHLZHYRRUE4CNT7QHWFDXJWK322XPUWO6RSFGB3FMI4H67OH5J', { type: 'address' });
  console.log('nativeToScVal(address) success:', scval.toXDR('base64'));
} catch (e) {
  console.log('nativeToScVal(address) failed:', e.message);
}

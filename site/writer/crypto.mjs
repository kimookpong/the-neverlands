const AAD = new TextEncoder().encode('the-neverlands-writer/v1');
function bytes(value) {
  if (typeof value !== 'string') throw new Error('Invalid envelope');
  return Uint8Array.from(atob(value), c => c.charCodeAt(0));
}
export async function decryptVault(envelope, password) {
  if (envelope?.version !== 1 || envelope.kdf !== 'PBKDF2-SHA256' ||
      envelope.cipher !== 'AES-256-GCM' || envelope.iterations !== 600000 ||
      typeof envelope.ciphertext !== 'string' || envelope.ciphertext.length > 28000000) {
    throw new Error('Invalid envelope');
  }
  const salt = bytes(envelope.salt), iv = bytes(envelope.iv);
  if (salt.length !== 16 || iv.length !== 12) throw new Error('Invalid envelope');
  const material = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveKey']);
  const key = await crypto.subtle.deriveKey({name:'PBKDF2', salt, iterations:envelope.iterations, hash:'SHA-256'}, material,
    {name:'AES-GCM', length:256}, false, ['decrypt']);
  const plaintext = await crypto.subtle.decrypt({name:'AES-GCM', iv, additionalData:AAD, tagLength:128}, key, bytes(envelope.ciphertext));
  const book = JSON.parse(new TextDecoder().decode(plaintext));
  if (book?.format !== 'neverlands-read-only-v1' || !Array.isArray(book.acts) || !book.acts.length || !Array.isArray(book.documents)) {
    throw new Error('Invalid book');
  }
  return book;
}

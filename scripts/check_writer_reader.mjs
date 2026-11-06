import assert from 'node:assert/strict';
import {createCipheriv, pbkdf2Sync} from 'node:crypto';
import {decryptVault} from '../site/writer/crypto.mjs';

const password='fixture-passphrase',salt=Buffer.alloc(16,1),iv=Buffer.alloc(12,2);
const fixture={format:'neverlands-read-only-v1',acts:[{id:'test',chapters:[]}],documents:[]};
const key=pbkdf2Sync(password,salt,600000,32,'sha256');
const cipher=createCipheriv('aes-256-gcm',key,iv);cipher.setAAD(Buffer.from('the-neverlands-writer/v1'));
const encrypted=Buffer.concat([cipher.update(JSON.stringify(fixture)),cipher.final(),cipher.getAuthTag()]);
const envelope={version:1,kdf:'PBKDF2-SHA256',iterations:600000,cipher:'AES-256-GCM',salt:salt.toString('base64'),iv:iv.toString('base64'),ciphertext:encrypted.toString('base64')};
assert.deepEqual(await decryptVault(envelope,password),fixture);
await assert.rejects(decryptVault(envelope,'incorrect-passphrase'));
const tampered=Buffer.from(encrypted);tampered[10]^=1;
await assert.rejects(decryptVault({...envelope,ciphertext:tampered.toString('base64')},password));
await assert.rejects(decryptVault({...envelope,iterations:1},password));
await assert.rejects(decryptVault({...envelope,iv:''},password));
console.log('PASS: browser-compatible decryption, wrong passwords, altered ciphertext and invalid envelopes');

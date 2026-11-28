// A photo picked or taken in the recipe form, made small enough to store.
// The server refuses anything over 300 KB (MAX_UPLOADED_PHOTO_BYTES in
// backend/app/api/recipes/crud.py).
export const MAX_PHOTO_BYTES = 300 * 1024;
const LONG_SIDE = 1600;
const STORED_TYPES = ["image/jpeg", "image/png", "image/webp"];

export interface NewPhoto {
  url: string;
  data: string;
  mimeType: string;
}

async function toBase64(blob: Blob): Promise<string> {
  const bytes = new Uint8Array(await blob.arrayBuffer());
  let binary = "";
  for (let i = 0; i < bytes.length; i += 0x8000)
    binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(binary);
}

function encode(
  picture: ImageBitmap,
  longSide: number,
  quality: number,
): Promise<Blob | null> {
  const scale = Math.min(1, longSide / Math.max(picture.width, picture.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(picture.width * scale));
  canvas.height = Math.max(1, Math.round(picture.height * scale));
  canvas
    .getContext("2d")
    ?.drawImage(picture, 0, 0, canvas.width, canvas.height);
  return new Promise((resolve) =>
    canvas.toBlob(resolve, "image/jpeg", quality),
  );
}

/** The file as a stored photo: as it is when small enough, otherwise a smaller JPEG. */
export async function shrinkPhoto(file: File): Promise<NewPhoto> {
  if (file.size <= MAX_PHOTO_BYTES && STORED_TYPES.includes(file.type))
    return { url: "", data: await toBase64(file), mimeType: file.type };

  const picture = await createImageBitmap(file).catch(() => {
    throw new Error("That file is not a picture this browser can open.");
  });
  try {
    // Lower the quality first, then the size, until it fits
    for (
      let longSide = LONG_SIDE;
      longSide >= 200;
      longSide = Math.round(longSide * 0.75)
    ) {
      for (let quality = 0.85; quality >= 0.45; quality -= 0.1) {
        const blob = await encode(picture, longSide, quality);
        if (blob && blob.size <= MAX_PHOTO_BYTES)
          return {
            url: "",
            data: await toBase64(blob),
            mimeType: "image/jpeg",
          };
      }
    }
  } finally {
    picture.close();
  }
  throw new Error("That photo could not be made small enough.");
}

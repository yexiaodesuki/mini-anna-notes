let anna = null;

export async function getRuntime() {

    if (anna) return anna;

    const sdk = await import(
        "/static/anna-apps/_sdk/latest/index.js"
    );

    anna = await sdk.AnnaAppRuntime.connect();

    return anna;
}
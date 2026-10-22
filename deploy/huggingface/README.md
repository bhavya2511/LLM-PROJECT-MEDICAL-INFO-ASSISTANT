# Deploy on Hugging Face Spaces (free, ~5 minutes of clicking)

You need a free Hugging Face account and your Groq key. The key is stored as a Space *secret*, never in code.

1. Sign up / log in at https://huggingface.co.
2. Go to https://huggingface.co/new-space. Name it `medical-assistant`, pick **Docker** as the SDK
   (choose "Blank"), hardware **CPU basic (free)**, visibility **Public**, then **Create Space**.
3. In the Space, open **Files → Add file → Create a new file**.
   - Name `Dockerfile`: paste the contents of `deploy/huggingface/Dockerfile` and commit.
   - Open the existing `README.md` in the Space, replace everything with `deploy/huggingface/SPACE_README.md`
     (the `---` block at the top is required) and commit.
4. Open **Settings → Variables and secrets → New secret**: name `GROQ_API_KEY`, value = your Groq key.
5. The Space builds automatically (first build about 10-15 minutes: it downloads MedlinePlus and the models and
   builds the index). When the status is **Running**, your public link is
   `https://huggingface.co/spaces/<your-username>/medical-assistant`.

To update after pushing new code to GitHub: Space **Settings → Factory rebuild**.

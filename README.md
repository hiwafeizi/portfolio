# My Portfolio

A simple, professional portfolio website built with HTML and CSS.

## Project Structure

- `index.html` - Main HTML file with portfolio content
- `styles.css` - Styling for the portfolio
- `README.md` - This file

## Features

- Clean, modern design
- Responsive layout (mobile-friendly)
- Navigation menu
- Hero section
- About section with skills
- Projects showcase
- Contact section
- Professional styling

## Customization

Before deploying, update the following:

1. **Portfolio Title**: Change "Portfolio" in the navbar and footer
2. **Your Name/Title**: Update the hero section h1 and subtitle
3. **About Content**: Edit the about section with your information
4. **Skills**: Add your actual skills in the skills list
5. **Projects**: Replace project descriptions with your actual projects
6. **Contact Information**: Update email and social media links

## Deploying to Cloudflare Pages (Free)

### Step 1: Create a GitHub Repository
1. Create a new repository on GitHub named `portfolio`
2. Push this code to your GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "Initial portfolio commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/portfolio.git
   git push -u origin main
   ```

### Step 2: Deploy to Cloudflare Pages
1. Go to [Cloudflare Pages](https://pages.cloudflare.com/)
2. Sign in with your Cloudflare account (create one if needed - it's free)
3. Click "Create a project"
4. Select "Connect to Git"
5. Authorize Cloudflare to access your GitHub repositories
6. Select your `portfolio` repository
7. Configure the build:
   - **Framework preset**: None
   - **Build command**: (leave empty)
   - **Build output directory**: / (root)
8. Click "Save and Deploy"

### Step 3: Custom Domain (Optional)
After deployment, you can:
- Use the free `*.pages.dev` domain assigned to your project
- Add a custom domain if you own one

## Local Testing

To test locally before deploying:
1. Open `index.html` directly in your browser, or
2. Use a local server:
   ```bash
   # Using Python 3
   python -m http.server 8000
   
   # Then visit http://localhost:8000
   ```

## Future Enhancements

Some ideas for enhancing your portfolio:
- Add more detailed project information and links
- Create individual project pages
- Add a blog section
- Implement dark mode toggle
- Add animations and transitions
- Create a contact form
- Add image galleries for projects
- Optimize for SEO

## License

This project is open source and available under the MIT License.

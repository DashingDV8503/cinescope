# CineScope: Detailed Technical Documentation

## 1. Introduction

This document provides a comprehensive technical breakdown of the CineScope web application. It is intended for a developer or an advanced AI tasked with creating a native or web replica of the app. The goal is to ensure the core logic, features, and user experience are replicated as faithfully as possible.

CineScope is a personal media tracker that allows users to manage their movie and TV show collections. All data is stored locally in the browser's Local Storage, with an optional Firebase cloud sync feature.

## 2. Data Models

Replicating the data structures is critical. The web app uses the following TypeScript interfaces, which should be mapped to corresponding data classes or structures in the target platform.

### 2.1 `Media` (The core object)

This is the central model for any movie or TV show in the user's list.

```typescript
// Location: src/lib/types.ts

export type MediaStatus = 'Watching' | 'Completed' | 'Plan to Watch' | 'Dropped';

export interface Media {
  id: number; // The Movie Database (TMDb) ID. This is the primary key.
  imdb_id?: string; // IMDb ID, used for fallbacks and linking.
  tvdb_id?: number; // TheTVDB ID, used for linking.
  title: string;
  year: string; // Just the year, e.g., "2011"
  type: 'movie' | 'series';
  poster_path: string | null; // Relative path to the poster image on TMDb.
  plot: string;
  genres: { id: number; name: string }[];
  vote_average: number; // TMDb user score (out of 10).
  status: MediaStatus; // User-set watch status.

  // Movie-specific (optional)
  runtime?: number; // In minutes.

  // Series-specific (optional)
  episode_run_time?: number[]; // Array of runtimes, often just one value. Use the first.
  number_of_seasons?: number;
  production_status?: string; // e.g., "Ended", "Returning Series"
  seasons?: SeasonProgress; // See below.
}
```

### 2.2 `SeasonProgress` and `Episode`

These models are nested within a `Media` object if `type` is `'series'`.

```typescript
// Location: src/lib/types.ts

export interface Episode {
  episode_number: number;
  name: string;
  vote_average: number; // TMDb rating for this specific episode.
}

export interface SeasonProgress {
  // The key is the season number as a string, e.g., "1", "2".
  [seasonNumber: string]: {
    episodesWatched: number;
    totalEpisodes: number;
    vote_average?: number; // Average rating for the season.
    episodes?: Episode[]; // Detailed list of episodes, fetched on demand.
  };
}
```

### 2.3 `UpcomingEpisode`

Used for the Calendar page to structure data from the TVMaze API.

```typescript
// Location: src/lib/types.ts
export interface UpcomingEpisode {
  showId: number;
  showTitle: string;
  backdropPath: string | null;
  airDate: string; // ISO 8601 string
  episodeName: string;
  episodeNumber: number;
  seasonNumber: number;
  episodeOverview: string;
  uniqueId?: string; // e.g., "{showId}-{season}-{episode}"
}
```

### 2.4 `User` (Firebase Auth) & `Backup` (Firestore)

Models for handling Firebase authentication and Firestore backups.

```typescript
// Location: src/lib/types.ts
export interface User {
  id: string; // A unique identifier (timestamp-based in the web app).
  name: string;
  email: string;
  avatar?: string; // URL to an avatar image.
}

export interface Backup {
  id: string; // Firestore document ID.
  timestamp: string; // ISO 8601 string.
}
```

## 3. Core Features & Implementation Logic

### 3.1 My List (Homepage) - `src/app/page.tsx`

This is the main screen, displaying the user's saved media.

#### **Functionality:**

1.  **Dual Views**: A toggle allows users to switch between:
    *   **Grid View (Default)**: Displays media posters in a responsive grid. This is the primary view for filtering and sorting. It separates Movies and TV Shows into distinct sections.
    *   **List View**: Displays media in horizontal carousels, also separated by "TV Shows" and "Movies". This view is for quick browsing and has no filter/sort controls.
2.  **Status Filtering (Grid View only)**: A dropdown allows users to show media matching a specific `MediaStatus` (`Watching`, `Completed`, etc.) or "All Statuses".
3.  **Search/Filter (Grid View only)**: A text input filters the list in real-time by `title`. The search is debounced by 300ms to avoid excessive re-renders while typing.
4.  **Sorting (Grid View only)**: A dropdown provides these sorting options on the filtered list:
    *   Title (A-Z, Z-A): Alphabetical sort on `media.title`.
    *   Year (Newest, Oldest): Numerical sort on `media.year`.
    *   Rating (Highest, Lowest): Numerical sort on `media.vote_average`.
5.  **Unwatched Episodes Badge**: On a series poster, if its `status` is "Watching", a badge shows the number of unwatched episodes.
    *   **Calculation Logic (`src/components/media-card.tsx`)**:
        ```javascript
        let unwatchedEpisodes = 0;
        if (media.type === 'series' && media.status === 'Watching' && media.seasons) {
          const totalEpisodes = Object.values(media.seasons).reduce((acc, season) => acc + season.totalEpisodes, 0);
          const watchedEpisodes = Object.values(media.seasons).reduce((acc, season) => acc + season.episodesWatched, 0);
          unwatchedEpisodes = totalEpisodes - watchedEpisodes;
        }
        // Display badge if unwatchedEpisodes > 0
        ```

#### **Implementation:**

*   The component `MediaListClient` (`src/components/media-list-client.tsx`) manages the state for filters, search terms, sorting, and view mode.
*   It uses a `useEffect` hook with a `storage` event listener to automatically re-render when the underlying data in `localStorage` changes.
*   A `useMemo` hook is used to efficiently compute the filtered and sorted list of media items. This calculation only re-runs when its dependencies (`items`, `debouncedSearchTerm`, `statusFilter`, `sortOption`) change.
*   The UI conditionally renders either the grid layout or the carousel-based list layout depending on the `view` state.

### 3.2 Search - `src/app/search/page.tsx`

This page allows users to find new media from external APIs.

#### **Functionality:**

1.  **Dual Search Logic**:
    *   **By IMDb ID**: If the search query matches the IMDb ID pattern (`tt` followed by digits), it directly calls the TMDb "Find" endpoint for a precise match.
    *   **By Title**: For any other query, it performs a title search.
2.  **Primary API (TMDb)**:
    *   A request is made to the TMDb "Multi-Search" endpoint: `https://api.themoviedb.org/3/search/multi?api_key=...&query=...`.
    *   This endpoint returns movies, TV shows, and people. The code filters out people and any media item without a `poster_path`.
3.  **Fallback API (OMDb)**:
    *   If the TMDb search returns zero results, the app automatically performs a fallback search using the OMDb API.
    *   **Step 1**: Search OMDb by title: `https://www.omdbapi.com/?s=...&apikey=...`. This returns a list of basic media items with IMDb IDs.
    *   **Step 2**: For each OMDb result, it uses the `imdbID` to query the TMDb "Find" endpoint: `https://api.themoviedb.org/3/find/{imdbID}?api_key=...&external_source=imdb_id`.
    *   This two-step fallback ensures all data in the app comes from a single source of truth (TMDb), maintaining data consistency.
4.  **De-duplication**: After fetching results from either API path, the results are de-duplicated based on their unique TMDb `id` to prevent the same show/movie from appearing multiple times.
5.  **Adding to List**:
    *   Search results are displayed in a grid of `ResultCard` components. Each item has a dropdown menu to "Add to List" with one of the four `MediaStatus` options.
    *   Once a status is chosen, the app fetches the *full details* for that item from TMDb (`/movie/{id}` or `/tv/{id}`) to create a complete `Media` object before saving it locally. This ensures all required fields are present.
    *   A check prevents adding an item that already exists in the user's list (by checking the `myListIds` state set).

#### **Implementation:**

*   The component uses the `useSearchParams` hook to allow deep-linking to search results (e.g., `/search?q=Inception`).
*   API keys are retrieved from local storage via `getApiKeys()`. The UI shows a prompt to set keys if they are missing.
*   The `handleSearch` function is a `useCallback` to prevent it from being recreated on every render. It orchestrates the API calls, fallback logic, and state updates.
*   The `myListIds` state is a `Set` for efficient O(1) lookups to check if an item has already been added to the user's list.
*   The `ResultCard` component is memoized with `React.memo` to optimize rendering performance, preventing re-renders of cards that haven't changed.

### 3.3 Media Details Page - `src/app/media/[type]/[id]/page.tsx`

This screen shows detailed information about a single media item.

#### **Functionality:**

1.  **Data Fetching & Enrichment**:
    *   On load, it fetches the media item from local storage using its ID.
    *   If the item is a series and is missing detailed data (like `production_status`, `tvdb_id`, or episode-specific data), it triggers a background fetch to TMDb to enrich the local data (`fetchMissingSeriesDetails`).
2.  **Information Display**: Shows poster, title, year, plot, genres, user rating (`vote_average`), and production status (for series). A blurred version of the poster is used as a background for aesthetic effect.
3.  **Status Management**: A dropdown allows the user to change the `MediaStatus` of the item. Changing a series' status to "Completed" automatically marks all episodes as watched. Changing it to "Plan to Watch" or "Dropped" resets watch progress to zero.
4.  **Remove Media**: A button with a confirmation dialog allows the user to delete the item from their local storage.
5.  **TV Show Progress Tracking**: This is a collapsible accordion section, only visible for series.
    *   It lists every season. For each season, it shows:
        *   Watched episodes / Total episodes (e.g., "5 / 10").
        *   Buttons to increment or decrement the watched count.
        *   A checkbox to mark the entire season as watched or unwatched.
    *   A "Save Progress" button persists these changes to the `Media` object in local storage.
    *   A line chart visualizes episodes watched per season.
6.  **Episode Ratings Grid**: For series where the data is available (it's fetched on-demand), this grid shows the user rating for every single episode, color-coded for quick visual reference (green for high, red for low).
7.  **External IDs**: Displays the IMDb, TMDb, and TVDb (for series) IDs and provides direct links to those sites.

#### **Implementation:**

*   The page uses a dynamic route `[type]/[id]`. The component `MediaDetailsClient` (`src/components/media-details-client.tsx`) handles all user interactions and state changes.
*   The progress tracker `TvProgress` (`src/components/tv-progress.tsx`) is loaded dynamically using `next/dynamic` to improve initial page load performance. It only loads when the accordion is opened.
*   All data updates (status change, progress save, removal) are delegated to functions in `src/lib/data.ts`, which handle the actual `localStorage` modification.

### 3.4 Statistics - `src/app/stats/page.tsx`

This page provides an overview of the user's viewing habits.

#### **Functionality & Calculation Logic:**

1.  **Prerequisite - Fetching Runtimes**: On page load, it silently iterates through the user's list and fetches missing `runtime` (for movies) or `episode_run_time` (for series) from TMDb. This ensures calculations are accurate. This is a background task that doesn't block the UI.

2.  **Total Watch Time**:
    *   This is the sum of time spent on media with `status` of **"Watching"** or **"Completed"**.
    *   **For Movies**: `total_time += movie.runtime`.
    *   **For TV Shows**:
        *   If `status` is **"Completed"**: `total_time += total_episodes_in_show * episode_run_time`.
        *   If `status` is **"Watching"**: `total_time += total_episodes_watched_in_show * episode_run_time`.
    *   The final value in minutes is formatted into a human-readable string (e.g., "X d Y h Z m").

3.  **Completed Movies & Completed Shows**: A simple count of media items where `type` is 'movie' or 'series' and `status` is 'Completed'.

4.  **Total Items**: A count of all items in the user's list.

5.  **Genre Breakdown**:
    *   Iterates through every item in the user's list.
    *   For each item, it iterates through its `genres` array.
    *   It maintains a map to count the occurrences of each genre name.
    *   The results are displayed in a horizontal bar chart, sorted from most frequent to least frequent.

#### **Implementation:**

*   The `calculateStats` function is wrapped in a `useMemo` hook to ensure calculations are only re-run when the `list` state changes.
*   The background fetching of runtimes is triggered in a `useEffect` hook, ensuring the UI can render immediately with potentially incomplete data, which is then updated once the fetches complete.

### 3.5 Upcoming Releases (Calendar) - `src/app/calendar/page.tsx`

This page shows a personalized schedule of upcoming episodes for shows the user is following.

#### **Functionality:**

1.  **Data Source**: This feature **exclusively uses the TVMaze API**, as its episode data is often more up-to-date.
2.  **Fetching Logic**:
    *   Gets all series from the user's list where `status` is "Watching" or "Plan to Watch".
    *   For each series, it searches TVMaze by title: `https://api.tvmaze.com/search/shows?q={title}`. It takes the first result.
    *   Using the TVMaze show ID, it fetches the full show details including all episodes: `https://api.tvmaze.com/shows/{tvmaze_id}?embed=episodes`.
    *   It filters the episodes list to include only those with an `airstamp` in the future.
    *   The resulting future episodes are grouped by show and sorted by the air date of their next upcoming episode.
3.  **Caching**: The page uses a "stale-while-revalidate" caching strategy with `sessionStorage`. When the page loads, it immediately displays cached data if available, then fetches fresh data in the background to update the view. This makes navigation feel instantaneous.

### 3.6 Discover - `src/app/discover/page.tsx`

This page helps users discover new content.

#### **Functionality:**

1.  **Data Source**: This feature uses the **Trakt.tv API** to get trending and popular lists and the **TMDb API** to enrich the data with posters and other details.
2.  **Fetching Logic**:
    *   It makes parallel requests to four Trakt.tv endpoints: `/movies/trending`, `/shows/trending`, `/movies/popular`, `/shows/popular`.
    *   For each list of results from Trakt, it extracts the TMDb IDs.
    *   It then makes batched requests to TMDb to fetch the full details for those IDs.
3.  **Display**: The results are displayed in four distinct grids: "Trending Movies," "Trending TV Shows," "Popular Movies," and "Popular TV Shows."
4.  **Caching**: Like the Calendar page, this page also uses a "stale-while-revalidate" `sessionStorage` cache to ensure instant page loads on subsequent visits within the same session.

### 3.7 Settings - `src/app/settings/page.tsx`

This is the control center for the application.

#### **Functionality:**

1.  **API Key Management**: Input fields for users to enter their personal TMDb, OMDb, and Trakt.tv API keys. These are required for most of the app's features to function.
2.  **API Status Check**: A button that pings the configuration/test endpoints of all required APIs (TMDb, OMDb, TVMaze, Trakt) to confirm they are operational.
3.  **Data Management (Local)**:
    *   **Export Data**: Serializes the entire local media list into a JSON file and prompts the user to save it.
    *   **Import Data**: Allows the user to select a JSON backup file. This file's content overwrites the current local list after a confirmation prompt.
    *   **Repair Library**: A powerful but potentially long-running operation. It iterates through every item in the user's list and re-fetches its data from TMDb. This is useful for filling in missing information while preserving the user's `status` and `seasons` progress.
4.  **Data Management (Online Sync)**:
    *   Requires Firebase login.
    *   **Create Cloud Backup**: Saves the current local list to Firestore under `users/{userId}/backups/{backupId}`. It keeps a maximum of 5 recent backups, automatically deleting the oldest when a new one is created. This is done in a single atomic `writeBatch` operation.
    *   **Show Backups & Restore**: Opens a dialog listing available cloud backups by timestamp. The user can select one to restore, which will overwrite their local data.
5.  **Appearance**: A theme toggle to switch between Light, Dark, and System modes.

#### **Implementation:**

*   It uses `react-hook-form` with `zodResolver` for robust form validation of the API keys.
*   Online sync functions (`backupDataToFirestore`, `getBackups`, `restoreDataFromFirestore` in `src/lib/data.ts`) handle all the Firestore logic. They are wrapped in `try...catch` blocks to handle errors gracefully, which are then shown to the user via toasts.

### 3.8 User Profile - `src/app/profile/page.tsx`

This page handles user authentication via Firebase.

#### **Functionality:**

1.  **Authentication**: Provides forms for email/password sign-up and login.
2.  **User State**: Once logged in, it displays the user's email and an avatar.
3.  **Logout**: A button to sign out of the Firebase session.

#### **Implementation:**

*   It uses the official Firebase Auth SDK.
*   The `onAuthStateChanged` listener is used in a `useEffect` hook to reactively update the UI based on the user's login state.
*   The user's authentication state is also used in the main app layout (`src/components/layout/app-layout.tsx`) to display user info in the sidebar and to control access to features like online sync.

---

This detailed guide provides a solid foundation for rebuilding the CineScope app. The key is to replicate the data flow and business logic accurately, especially around the API interactions, state management, caching strategies, and statistics calculations.

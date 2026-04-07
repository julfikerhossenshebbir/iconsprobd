import { loadIcons, CATEGORIES } from '@/lib/icons';
import IconLibrary from '@/app/components/IconLibrary';

export default function Home() {
  const data      = loadIcons();
  const allIcons  = data.icons;
  const iconW     = data.width  ?? 24;
  const iconH     = data.height ?? 24;
  const prefix    = data.prefix ?? 'icons';
  const totalCount = Object.keys(allIcons).length;

  // Build icon list for the client: name + body string
  const iconList = Object.entries(allIcons).map(([name, detail]) => ({
    name,
    body: detail.body,
  }));

  return (
    <IconLibrary
      iconList={iconList}
      iconW={iconW}
      iconH={iconH}
      prefix={prefix}
      totalCount={totalCount}
      categories={CATEGORIES}
    />
  );
}

import PlayerProfile from "@/components/PlayerProfile";

export default function PlayerPage({ params }: { params: { id: string } }) {
  return <PlayerProfile playerId={params.id} />;
}
